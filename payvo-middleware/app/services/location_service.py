"""
Enhanced Location Service for MCC Prediction
Integrates Google Places API and Foursquare API for precise business location analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import hashlib
from datetime import datetime, timedelta
import os

import googlemaps
import httpx
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
import h3
import numpy as np

from ..core.config import settings
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class LocationService:
    """Enhanced location service with real API integrations"""
    
    def __init__(self):
        self.google_maps_client = None
        self.foursquare_api_key = None
        self.cache_duration = timedelta(hours=6)  # Cache results for 6 hours
        self.supabase = None
        
    async def initialize(self):
        """Initialize API clients and database connections"""
        try:
            # Initialize Google Maps client
            google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
            if google_api_key:
                self.google_maps_client = googlemaps.Client(key=google_api_key)
                logger.info("Google Places API initialized")
            else:
                logger.warning("Google Places API key not found")
            
            # Initialize Foursquare API
            self.foursquare_api_key = os.getenv('FOURSQUARE_API_KEY')
            if self.foursquare_api_key:
                logger.info("Foursquare API initialized")
            else:
                logger.warning("Foursquare API key not found")
            
            # Initialize database
            self.supabase = await get_supabase_client()
            await self._create_location_tables()
            
        except Exception as e:
            logger.error(f"Error initializing LocationService: {str(e)}")
    
    async def _create_location_tables(self):
        """Create necessary database tables for location data"""
        try:
            # Create business locations cache table
            await self.supabase.table('business_locations').select('*').limit(1).execute()
        except:
            # Table doesn't exist, create it
            logger.info("Creating business_locations table")
            # In practice, you'd use proper database migrations
    
    async def analyze_business_district(self, lat: float, lng: float, radius: int = 500) -> Dict[str, Any]:
        """
        Comprehensive business district analysis using multiple data sources
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters (default 500m)
        
        Returns:
            Detailed business district analysis
        """
        try:
            # Check cache first
            cache_key = self._generate_location_cache_key(lat, lng, radius)
            cached_result = await self._get_cached_analysis(cache_key)
            if cached_result:
                return cached_result
            
            # Gather data from multiple sources
            google_places = await self._get_google_places_data(lat, lng, radius)
            foursquare_venues = await self._get_foursquare_data(lat, lng, radius)
            historical_data = await self._get_historical_transaction_data(lat, lng, radius)
            
            # Combine and analyze data
            analysis = await self._combine_location_analyses(
                google_places, foursquare_venues, historical_data, lat, lng
            )
            
            # Cache the result
            await self._cache_analysis(cache_key, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in business district analysis: {str(e)}")
            return self._get_fallback_analysis()
    
    async def _get_google_places_data(self, lat: float, lng: float, radius: int) -> Dict[str, Any]:
        """Get business data from Google Places API"""
        if not self.google_maps_client:
            return {"businesses": [], "density_score": 0.0}
        
        try:
            # Search for nearby places
            places_result = self.google_maps_client.places_nearby(
                location=(lat, lng),
                radius=radius,
                type=None  # Get all types
            )
            
            businesses = []
            business_types = {}
            total_rating_sum = 0
            rated_businesses = 0
            
            for place in places_result.get('results', []):
                place_types = place.get('types', [])
                rating = place.get('rating', 0)
                
                # Extract business info
                business = {
                    'name': place.get('name', ''),
                    'types': place_types,
                    'rating': rating,
                    'price_level': place.get('price_level', 0),
                    'place_id': place.get('place_id', ''),
                    'location': place.get('geometry', {}).get('location', {}),
                    'mcc_category': self._google_types_to_mcc_category(place_types)
                }
                businesses.append(business)
                
                # Count business types
                for business_type in place_types:
                    if business_type not in ['establishment', 'point_of_interest']:
                        business_types[business_type] = business_types.get(business_type, 0) + 1
                
                # Calculate average rating
                if rating > 0:
                    total_rating_sum += rating
                    rated_businesses += 1
            
            avg_rating = total_rating_sum / rated_businesses if rated_businesses > 0 else 0
            
            return {
                'businesses': businesses,
                'business_count': len(businesses),
                'business_types': business_types,
                'density_score': min(len(businesses) / 50.0, 1.0),  # Normalize to 0-1
                'average_rating': avg_rating,
                'commercial_indicators': self._analyze_google_commercial_indicators(business_types)
            }
            
        except Exception as e:
            logger.error(f"Error fetching Google Places data: {str(e)}")
            return {"businesses": [], "density_score": 0.0}
    
    async def _get_foursquare_data(self, lat: float, lng: float, radius: int) -> Dict[str, Any]:
        """Get venue data from Foursquare API"""
        if not self.foursquare_api_key:
            return {"venues": [], "density_score": 0.0}
        
        try:
            async with httpx.AsyncClient() as client:
                # Foursquare Places API v3
                url = "https://api.foursquare.com/v3/places/search"
                headers = {
                    "Authorization": self.foursquare_api_key,  # Direct API key, no Bearer prefix
                    "Accept": "application/json"
                }
                params = {
                    "ll": f"{lat},{lng}",
                    "radius": radius,
                    "limit": 50,
                    "fields": "name,categories,rating,price,location,stats"
                }
                
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                venues = []
                categories = {}
                
                for venue in data.get('results', []):
                    venue_categories = venue.get('categories', [])
                    
                    venue_info = {
                        'name': venue.get('name', ''),
                        'categories': [cat.get('name', '') for cat in venue_categories],
                        'rating': venue.get('rating', 0),
                        'price': venue.get('price', 0),
                        'location': venue.get('location', {}),
                        'stats': venue.get('stats', {}),
                        'mcc_category': self._foursquare_categories_to_mcc(venue_categories)
                    }
                    venues.append(venue_info)
                    
                    # Count categories
                    for cat in venue_categories:
                        cat_name = cat.get('name', '')
                        categories[cat_name] = categories.get(cat_name, 0) + 1
                
                return {
                    'venues': venues,
                    'venue_count': len(venues),
                    'categories': categories,
                    'density_score': min(len(venues) / 40.0, 1.0),  # Normalize to 0-1
                    'commercial_indicators': self._analyze_foursquare_commercial_indicators(categories)
                }
                
        except Exception as e:
            logger.error(f"Error fetching Foursquare data: {str(e)}")
            return {"venues": [], "density_score": 0.0}
    
    async def _get_historical_transaction_data(self, lat: float, lng: float, radius: int) -> Dict[str, Any]:
        """Get historical transaction data for the area"""
        try:
            # Create a geohash for the area
            location_hash = self._generate_location_hash(lat, lng, precision=7)  # ~150m precision
            
            # Query historical data from our database
            if self.supabase:
                result = await self.supabase.table('transaction_history').select(
                    'mcc, confidence, method, created_at, location_hash'
                ).eq('location_hash', location_hash).execute()
                
                transactions = result.data if result.data else []
                
                # Analyze historical patterns
                mcc_counts = {}
                confidence_sum = {}
                total_transactions = len(transactions)
                
                for tx in transactions:
                    mcc = tx.get('mcc', '')
                    confidence = tx.get('confidence', 0)
                    
                    mcc_counts[mcc] = mcc_counts.get(mcc, 0) + 1
                    confidence_sum[mcc] = confidence_sum.get(mcc, 0) + confidence
                
                # Calculate weighted MCCs
                mcc_patterns = {}
                for mcc, count in mcc_counts.items():
                    frequency = count / total_transactions
                    avg_confidence = confidence_sum[mcc] / count
                    mcc_patterns[mcc] = {
                        'frequency': frequency,
                        'avg_confidence': avg_confidence,
                        'count': count
                    }
                
                return {
                    'total_transactions': total_transactions,
                    'mcc_patterns': mcc_patterns,
                    'dominant_mcc': max(mcc_counts, key=mcc_counts.get) if mcc_counts else None,
                    'historical_confidence': sum(confidence_sum.values()) / sum(mcc_counts.values()) if mcc_counts else 0
                }
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
        
        return {'total_transactions': 0, 'mcc_patterns': {}}
    
    async def _combine_location_analyses(self, google_data: Dict, foursquare_data: Dict, 
                                       historical_data: Dict, lat: float, lng: float) -> Dict[str, Any]:
        """Combine all location analysis data into a comprehensive result"""
        
        # Calculate overall commercial score
        google_score = google_data.get('density_score', 0) * 0.4
        foursquare_score = foursquare_data.get('density_score', 0) * 0.4
        historical_score = min(historical_data.get('total_transactions', 0) / 100.0, 1.0) * 0.2
        
        overall_commercial_score = google_score + foursquare_score + historical_score
        
        # Determine primary business types
        all_business_types = []
        
        # Add Google business types
        google_types = google_data.get('business_types', {})
        for btype, count in google_types.items():
            all_business_types.extend([btype] * count)
        
        # Add Foursquare categories
        foursquare_cats = foursquare_data.get('categories', {})
        for cat, count in foursquare_cats.items():
            all_business_types.extend([cat.lower().replace(' ', '_')] * count)
        
        # Find dominant business type
        if all_business_types:
            from collections import Counter
            business_counter = Counter(all_business_types)
            dominant_type = business_counter.most_common(1)[0][0]
        else:
            dominant_type = "unknown"
        
        # Predict MCC based on combined data
        predicted_mcc = await self._predict_mcc_from_combined_data(
            google_data, foursquare_data, historical_data
        )
        
        return {
            'commercial_score': min(overall_commercial_score, 1.0),
            'business_density': self._categorize_density(overall_commercial_score),
            'primary_business_types': list(set(all_business_types[:5])),  # Top 5 unique types
            'dominant_business_type': dominant_type,
            'google_data': google_data,
            'foursquare_data': foursquare_data,
            'historical_data': historical_data,
            'predicted_mcc': predicted_mcc,
            'location_precision': self._calculate_location_precision(lat, lng),
            'confidence_factors': {
                'google_api_available': bool(self.google_maps_client),
                'foursquare_api_available': bool(self.foursquare_api_key),
                'historical_data_available': historical_data.get('total_transactions', 0) > 0,
                'combined_business_count': google_data.get('business_count', 0) + foursquare_data.get('venue_count', 0)
            }
        }
    
    async def _predict_mcc_from_combined_data(self, google_data: Dict, foursquare_data: Dict, historical_data: Dict) -> Dict[str, Any]:
        """Predict MCC from combined location data"""
        
        # Start with historical data if available
        historical_mcc = historical_data.get('dominant_mcc')
        if historical_mcc and historical_data.get('total_transactions', 0) >= 5:
            return {
                'mcc': historical_mcc,
                'confidence': min(0.9, historical_data.get('historical_confidence', 0.5) + 0.2),
                'source': 'historical_data'
            }
        
        # Analyze business types from APIs
        business_type_scores = {}
        
        # Google Places analysis
        for business in google_data.get('businesses', []):
            mcc_category = business.get('mcc_category')
            if mcc_category:
                score = business.get('rating', 3.0) / 5.0  # Normalize rating
                business_type_scores[mcc_category] = business_type_scores.get(mcc_category, 0) + score
        
        # Foursquare analysis
        for venue in foursquare_data.get('venues', []):
            mcc_category = venue.get('mcc_category')
            if mcc_category:
                score = venue.get('rating', 6.0) / 10.0  # Normalize rating
                business_type_scores[mcc_category] = business_type_scores.get(mcc_category, 0) + score
        
        if business_type_scores:
            best_category = max(business_type_scores, key=business_type_scores.get)
            total_score = sum(business_type_scores.values())
            confidence = min(0.85, business_type_scores[best_category] / total_score)
            
            return {
                'mcc': best_category,
                'confidence': confidence,
                'source': 'combined_apis'
            }
        
        # Fallback
        return {
            'mcc': '5999',
            'confidence': 0.3,
            'source': 'fallback'
        }
    
    def _google_types_to_mcc_category(self, types: List[str]) -> Optional[str]:
        """Convert Google Places types to Stripe Issuing MCC categories"""
        # Complete mapping using ALL official Stripe Issuing MCC codes
        type_patterns = {
            # Food & Dining
            ('restaurant', 'meal_delivery', 'meal_takeaway', 'food'): '5812',  # Eating Places, Restaurants
            ('fast_food', 'quick_service'): '5814',  # Fast Food Restaurants
            ('cafe', 'bakery'): '5462',  # Bakeries
            ('bar', 'night_club', 'liquor_store'): '5921',  # Package Stores-Beer, Wine, and Liquor
            ('caterer', 'catering'): '5811',  # Caterers
            
            # Agriculture & Farming
            ('farm', 'agriculture', 'agricultural'): '0763',  # Agricultural Cooperative
            ('veterinary',): '0742',  # Veterinary Services
            ('landscaping', 'lawn', 'garden'): '0780',  # Landscaping Services
            
            # Construction & Contractors - Complete Coverage
            ('general_contractor', 'construction'): '1520',  # General Contractors
            ('carpentry', 'carpenter'): '1750',  # Carpentry Services
            ('concrete', 'cement'): '1771',  # Concrete Work Services
            ('electrical', 'electrician'): '1731',  # Electrical Contractors
            ('glass', 'glazing'): '1740',  # Masonry, Stonework, and Plaster
            ('heating', 'hvac', 'air_conditioning'): '1711',  # Plumbing, Heating, Air-Conditioning
            ('insulation',): '1799',  # Special Trade Contractors
            ('painting', 'painter'): '1721',  # Painting, Paperhanging, Decorating
            ('plumbing', 'plumber'): '1711',  # Plumbing, Heating, Air-Conditioning
            ('roofing', 'roofer'): '1761',  # Roofing/Siding, Sheet Metal
            ('welding', 'welder'): '7692',  # Welding Repair
            
            # Manufacturing & Wholesale - Complete Coverage
            ('chemical', 'industrial'): '5169',  # Chemicals and Allied Products
            ('commercial_equipment',): '5046',  # Commercial Equipment
            ('computer_wholesale', 'tech_wholesale'): '5045',  # Computers, Peripherals, and Software
            ('construction_materials',): '5039',  # Construction Materials
            ('drug_wholesale', 'pharmaceutical'): '5122',  # Drugs, Drug Proprietaries, and Druggist Sundries
            ('electrical_parts',): '5065',  # Electrical Parts and Equipment
            ('footwear_wholesale',): '5139',  # Commercial Footwear
            ('furniture_wholesale',): '5021',  # Office and Commercial Furniture
            ('hardware_wholesale',): '5072',  # Hardware, Equipment, and Supplies
            ('jewelry_wholesale',): '5094',  # Precious Stones and Metals, Watches and Jewelry
            ('lumber', 'building_supplies'): '5211',  # Lumber, Building Materials Stores
            ('metals', 'steel'): '5051',  # Metal Service Centers
            ('office_supplies_wholesale',): '5111',  # Stationery, Office Supplies, Printing and Writing Paper
            ('paint_wholesale',): '5198',  # Paints, Varnishes, and Supplies
            ('paper', 'paper_products'): '5111',  # Stationery, Office Supplies, Printing and Writing Paper
            ('petroleum_wholesale',): '5172',  # Petroleum and Petroleum Products
            ('photographic_wholesale',): '5044',  # Photographic, Photocopy, Microfilm Equipment, and Supplies
            ('plumbing_wholesale',): '5074',  # Plumbing, Heating Equipment, and Supplies
            ('textile_wholesale',): '5131',  # Piece Goods, Notions, and Other Dry Goods
            ('tobacco_wholesale',): '5194',  # Tobacco and Tobacco Products
            
            # Publishing & Media
            ('book_wholesale', 'publishing'): '5192',  # Books, Periodicals, and Newspapers
            ('printing', 'typesetting'): '2791',  # Typesetting, Plate Making, and Related Services
            ('newspaper', 'magazine'): '5192',  # Books, Periodicals, and Newspapers
            
            # Retail - Complete Coverage
            ('gas_station',): '5541',  # Service Stations
            ('automated_fuel',): '5542',  # Automated Fuel Dispensers
            ('grocery_or_supermarket', 'supermarket'): '5411',  # Grocery Stores, Supermarkets
            ('convenience', 'corner_store'): '5499',  # Miscellaneous Food Stores - Convenience Stores and Specialty Markets
            ('candy', 'confectionery'): '5441',  # Candy, Nut, and Confectionery Stores
            ('clothing_store',): '5651',  # Family Clothing Stores
            ('mens_clothing',): '5611',  # Men's and Boys' Clothing and Accessories Stores
            ('womens_clothing',): '5621',  # Women's Ready-To-Wear Stores
            ('childrens_clothing',): '5641',  # Children's and Infants' Wear Stores
            ('womens_accessories',): '5631',  # Women's Accessory and Specialty Shops
            ('sports_apparel',): '5655',  # Sports and Riding Apparel Stores
            ('uniform',): '5137',  # Uniforms, Commercial Clothing
            ('shoe_store',): '5661',  # Shoe Stores
            ('electronics_store', 'computer'): '5732',  # Electronics Stores
            ('computer_software',): '5734',  # Computer Software Stores
            ('record_store', 'music'): '5735',  # Record Stores
            ('department_store',): '5311',  # Department Stores
            ('discount_store',): '5310',  # Discount Stores
            ('variety_store',): '5331',  # Variety Stores
            ('wholesale_club',): '5300',  # Wholesale Clubs
            ('pharmacy',): '5912',  # Drug Stores and Pharmacies
            ('furniture_store',): '5712',  # Furniture, Home Furnishings, and Equipment Stores, Except Appliances
            ('home_supply', 'home_improvement'): '5200',  # Home Supply Warehouse Stores
            ('appliance',): '5722',  # Household Appliance Stores
            ('jewelry_store',): '5944',  # Jewelry Stores, Watches, Clocks, and Silverware Stores
            ('book_store',): '5942',  # Book Stores
            ('stationery', 'office_supply'): '5943',  # Stationery Stores, Office, and School Supply Stores
            ('sporting_goods_store',): '5941',  # Sporting Goods Stores
            ('toy_store', 'hobby'): '5945',  # Hobby, Toy, and Game Shops
            ('camera_store',): '5946',  # Camera and Photographic Supply Stores
            ('gift_shop',): '5947',  # Gift, Card, Novelty, and Souvenir Shops
            ('fabric', 'sewing'): '5949',  # Sewing, Needlework, Fabric, and Piece Goods Stores
            ('hardware_store',): '5251',  # Hardware Stores
            ('paint_store',): '5231',  # Glass, Paint, and Wallpaper Stores
            ('lumber_yard',): '5211',  # Lumber, Building Materials Stores
            ('nursery', 'garden_center'): '5261',  # Nurseries, Lawn and Garden Supply Stores
            ('pet',): '5995',  # Pet Shops, Pet Food, and Supplies
            ('florist',): '5992',  # Florists
            ('bicycle',): '5940',  # Bicycle Shops
            ('motorcycle',): '5571',  # Motorcycle Shops and Dealers
            ('boat',): '5551',  # Boat Dealers
            ('rv', 'recreational_vehicle'): '5561',  # Recreational Vehicle Dealers
            ('snowmobile',): '5598',  # Snowmobile Dealers
            ('art', 'gallery'): '5971',  # Art Dealers and Galleries
            ('artist_supply',): '5970',  # Artists Supply and Craft Shops
            ('antique',): '5932',  # Antique Shops
            ('antique_reproduction',): '5937',  # Antique Reproductions
            ('used_merchandise',): '5931',  # Used Merchandise and Secondhand Stores
            ('pawn',): '5933',  # Pawn Shops
            ('cigar',): '5993',  # Cigar Stores and Stands
            ('cosmetic',): '5977',  # Cosmetic Stores
            ('typewriter',): '5978',  # Typewriter Stores
            ('wig',): '5698',  # Wig and Toupee Stores
            ('religious_goods',): '5973',  # Religious Goods Stores
            ('stamp_coin',): '5972',  # Stamp and Coin Stores
            ('orthopedic',): '5976',  # Orthopedic Goods - Prosthetic Devices
            ('optical',): '5976',  # Opticians, Eyeglasses
            ('tent', 'awning'): '5998',  # Tent and Awning Shops
            ('swimming_pool',): '5996',  # Swimming Pools Sales
            ('miscellaneous_retail',): '5999',  # Miscellaneous Retail
            
            # Automotive - Complete Coverage
            ('car_dealer',): '5511',  # Car and Truck Dealers (New & Used) Sales, Service, Repairs Parts and Leasing
            ('used_car',): '5521',  # Car and Truck Dealers (Used Only) Sales, Service, Repairs Parts and Leasing
            ('tire',): '5532',  # Automotive Tire Stores
            ('auto_parts',): '5533',  # Automotive Parts and Accessories Stores
            ('auto_and_home_supply',): '5531',  # Auto and Home Supply Stores
            ('car_rental',): '7512',  # Car Rental Agencies
            ('truck_rental',): '7513',  # Truck/Utility Trailer Rentals
            ('recreational_vehicle_rental',): '7519',  # Recreational Vehicle Rentals
            ('auto_body',): '7531',  # Auto Body Repair Shops
            ('tire_repair',): '7534',  # Tire Retreading and Repair
            ('auto_paint',): '7535',  # Auto Paint Shops
            ('auto_service',): '7538',  # Auto Service Shops
            ('car_wash',): '7542',  # Car Washes
            ('towing',): '7549',  # Towing Services
            
            # Financial Services - Complete Coverage
            ('bank', 'atm'): '6011',  # Automated Cash Disburse
            ('quasi_cash',): '6051',  # Quasi Cash - Merchant
            ('financial_institution',): '6012',  # Financial Institutions
            ('credit_reporting',): '7321',  # Credit Reporting Agencies
            ('collection_agency',): '7322',  # Collection Agencies
            ('debt_counseling',): '7299',  # Miscellaneous Personal Services
            ('check_cashing',): '6051',  # Quasi Cash - Merchant
            ('money_order',): '4829',  # Wires, Money Orders
            ('security_broker',): '6211',  # Security Brokers/Dealers
            ('insurance',): '6300',  # Insurance Sales, Underwriting, and Premiums
            ('real_estate',): '6513',  # Real Estate Agents and Managers - Rentals
            
            # Transportation - Complete Coverage
            ('airline',): '4511',  # Airlines, Air Carriers
            ('train', 'railway'): '4112',  # Passenger Railways
            ('bus',): '4131',  # Bus Lines
            ('taxi',): '4121',  # Taxicabs/Limousines
            ('limousine',): '4121',  # Taxicabs/Limousines
            ('ferry',): '4111',  # Commuter Transport, Ferries
            ('commuter_transport',): '4111',  # Commuter Transport, Ferries
            ('ambulance',): '4119',  # Ambulance Services
            ('courier',): '4215',  # Courier Services
            ('freight',): '4214',  # Motor Freight Carriers and Trucking - Local and Long Distance, Moving and Storage Companies, and Local Delivery Services
            ('moving',): '4214',  # Motor Freight Carriers and Trucking
            ('storage',): '4225',  # Public Warehousing and Storage
            ('boat_rental',): '4457',  # Boat Rentals and Leases
            ('marina',): '4468',  # Marinas, Service and Supplies
            ('airport',): '4582',  # Airports, Flying Fields
            ('tolls', 'bridge'): '4784',  # Tolls/Bridge Fees
            ('transportation_service',): '4789',  # Transportation Services
            ('parking',): '7523',  # Parking Lots, Garages
            
            # Communication & Utilities - Complete Coverage
            ('telephone', 'telecom'): '4814',  # Telecommunication Services
            ('telegraph',): '4821',  # Telegraph Services
            ('cable', 'satellite'): '4899',  # Cable, Satellite, and Other Pay Television and Radio
            ('computer_network',): '4816',  # Computer Network Services
            ('telecommunication_equipment',): '4812',  # Telecommunication Equipment and Telephone Sales
            ('utility',): '4900',  # Utilities
            ('electric', 'gas_utility', 'water'): '4900',  # Utilities
            
            # Lodging & Travel - Complete Coverage
            ('hotel', 'lodging'): '7011',  # Hotels, Motels, and Resorts
            ('timeshare',): '7012',  # Timeshares
            ('campground',): '7033',  # Trailer Parks, Campgrounds
            ('sporting_camp',): '7032',  # Sporting/Recreation Camps
            ('travel_agency',): '4722',  # Travel Agencies, Tour Operators
            ('tui_travel',): '4723',  # TUI Travel - Germany
            
            # Health & Medical - Complete Coverage
            ('doctor',): '8011',  # Doctors of Medicine
            ('dentist',): '8021',  # Dentists, Orthodontists
            ('osteopath',): '8031',  # Osteopaths
            ('chiropractor',): '8041',  # Chiropractors
            ('optometrist',): '8042',  # Optometrists, Ophthalmologist
            ('optician',): '8043',  # Opticians, Eyeglasses
            ('podiatrist',): '8049',  # Chiropodists, Podiatrists
            ('nursing',): '8050',  # Nursing/Personal Care
            ('hospital',): '8062',  # Hospitals
            ('medical_lab',): '8071',  # Medical and Dental Laboratories
            ('medical_service',): '8099',  # Medical Services and Health Practitioners
            ('veterinary',): '0742',  # Veterinary Services
            
            # Beauty & Personal Care - Complete Coverage
            ('beauty_salon', 'hair_care', 'spa'): '7230',  # Barber and Beauty Shops
            ('massage', 'health_spa'): '7298',  # Health and Beauty Spas
            ('laundry',): '7216',  # Dry Cleaners
            ('carpet_cleaning',): '7217',  # Carpet/Upholstery Cleaning
            ('photo_finishing',): '7395',  # Photo Developing
            ('shoe_repair',): '7251',  # Shoe Repair/Hat Cleaning
            ('watch_repair',): '7631',  # Watch/Jewelry Repair
            ('appliance_repair',): '7629',  # Small Appliance Repair
            ('clothing_rental',): '7296',  # Clothing Rental
            ('formal_wear',): '5697',  # Tailors, Alterations
            ('tailor',): '5697',  # Tailors, Alterations
            
            # Fitness & Recreation - Complete Coverage
            ('gym', 'health', 'fitness'): '7997',  # Membership Clubs (Sports, Recreation, Athletic), Country Clubs, and Private Golf Courses
            ('country_club',): '7997',  # Country Clubs
            ('sports_club',): '7941',  # Sports Clubs/Fields
            ('golf',): '7997',  # Country Clubs
            ('bowling',): '7933',  # Bowling Alleys
            ('billiard',): '7932',  # Billiard/Pool Establishments
            ('dance_hall',): '7911',  # Dance Halls, Studios, and Schools
            ('pool_hall',): '7932',  # Billiard/Pool Establishments
            
            # Entertainment - Complete Coverage
            ('movie_theater',): '7832',  # Motion Picture Theaters
            ('video_rental',): '7841',  # Video Tape Rental Stores
            ('amusement_park',): '7996',  # Amusement Parks/Carnivals
            ('carnival',): '7996',  # Amusement Parks/Carnivals
            ('casino', 'gambling'): '7995',  # Betting/Casino Gambling
            ('arcade',): '7994',  # Video Game Arcades
            ('video_game_supply',): '7993',  # Video Amusement Game Supplies
            ('aquarium', 'zoo'): '7998',  # Aquariums
            ('tourist_attraction',): '7991',  # Tourist Attractions and Exhibits
            ('band', 'orchestra'): '7929',  # Bands, Orchestras
            ('theatrical_ticket',): '7922',  # Theatrical Ticket Agencies
            ('picture_production',): '7829',  # Picture/Video Production
            
            # Professional Services - Complete Coverage
            ('lawyer', 'legal'): '8111',  # Legal Services, Attorneys
            ('accounting',): '8931',  # Accounting/Bookkeeping Services
            ('advertising',): '7311',  # Advertising Services
            ('architect',): '8911',  # Architectural/Surveying Services
            ('consulting',): '7392',  # Consulting, Public Relations
            ('employment',): '7361',  # Employment/Temp Agencies
            ('business_service',): '7399',  # Business Services
            ('computer_programming',): '7372',  # Computer Programming
            ('computer_repair',): '7379',  # Computer Repair
            ('data_processing',): '7374',  # Computer Integrated Systems Design
            ('information_retrieval',): '7375',  # Information Retrieval Services
            ('management_consulting',): '7392',  # Consulting, Public Relations
            ('public_relations',): '7392',  # Consulting, Public Relations
            ('secretarial',): '7339',  # Secretarial Support Services
            ('stenographic',): '7339',  # Secretarial Support Services
            ('telephone_answering',): '7389',  # Business Services
            ('credit_reporting',): '7321',  # Credit Reporting Agencies
            ('collection',): '7322',  # Collection Agencies
            ('protective_security',): '7393',  # Detective Agencies, Protective Agencies, and Security Services, Including Armored Cars
            ('exterminating',): '7342',  # Exterminating Services
            ('janitorial', 'cleaning'): '7349',  # Cleaning and Maintenance
            ('window_cleaning',): '7349',  # Cleaning and Maintenance
            ('landscaping',): '0780',  # Landscaping Services
            ('welding',): '7692',  # Welding Repair
            ('specialty_cleaning',): '2842',  # Specialty Cleaning
            ('photographic_studio',): '7221',  # Photographic Studios
            ('portrait_studio',): '7221',  # Photographic Studios
            ('commercial_photography',): '7333',  # Commercial Photography, Art and Graphics
            ('art_school',): '8299',  # Schools and Educational Services
            ('dance_school',): '8299',  # Schools and Educational Services
            ('music_school',): '8299',  # Schools and Educational Services
            ('correspondence_school',): '8241',  # Correspondence Schools
            ('trade_school',): '8249',  # Vocational/Trade Schools
            ('business_school',): '8244',  # Business/Secretarial Schools
            
            # Education - Complete Coverage
            ('school', 'university', 'college'): '8220',  # Colleges, Universities
            ('elementary_school',): '8211',  # Elementary, Secondary Schools
            ('secondary_school',): '8211',  # Elementary, Secondary Schools
            ('childcare',): '8351',  # Child Care Services
            ('kindergarten',): '8351',  # Child Care Services
            ('preschool',): '8351',  # Child Care Services
            ('educational_service',): '8299',  # Schools and Educational Services
            ('library',): '8231',  # Correspondence Schools
            
            # Government & Public Services - Complete Coverage
            ('government',): '9399',  # Government Services
            ('federal_government',): '9405',  # U.S. Federal Government Agencies or Departments
            ('post_office',): '9402',  # Postal Services - Government Only
            ('court',): '9211',  # Court Costs, Including Alimony and Child Support
            ('fine',): '9222',  # Fines - Government Administrative Entities
            ('bail',): '9223',  # Bail and Bond Payments
            ('tax_payment',): '9311',  # Tax Payments - Government Agencies
            ('motor_vehicle_department',): '9399',  # Government Services
            ('license',): '9399',  # Government Services
            
            # Religious & Charitable - Complete Coverage
            ('church', 'religious'): '8661',  # Religious Organizations
            ('charity',): '8398',  # Charitable and Social Service Organizations - Fundraising
            ('political',): '8651',  # Political Organizations
            ('civic_organization',): '8641',  # Civic, Social, Fraternal Associations
            ('labor_union',): '8699',  # Membership Organizations
            ('professional_organization',): '8699',  # Membership Organizations
            ('automobile_association',): '8675',  # Automobile Associations
            
            # Specialty Services
            ('buying_service',): '7278',  # Buying/Shopping Services
            ('counseling',): '7277',  # Counseling Services
            ('dating_service',): '7273',  # Dating/Escort Services
            ('diet_service',): '7299',  # Miscellaneous Personal Services
            ('drug_treatment',): '8093',  # Specialty Outpatient Facilities
            ('funeral',): '7261',  # Funeral Service and Crematories
            ('marriage_counseling',): '7277',  # Counseling Services
            ('tax_preparation',): '7276',  # Tax Preparation Services
            ('testing_lab',): '8734',  # Testing Laboratories
            
            # Quick Copy & Printing
            ('quick_copy',): '7338',  # Quick Copy, Repro, and Blueprint
            ('blueprint',): '7338',  # Quick Copy, Repro, and Blueprint
            ('printing',): '2791',  # Typesetting, Plate Making, and Related Services
        }
        
        for place_type in types:
            # Check each pattern group
            for patterns, mcc in type_patterns.items():
                if any(pattern in place_type for pattern in patterns):
                    return mcc
        
        # Default retail categories
        retail_indicators = ['store', 'shop', 'shopping']
        for place_type in types:
            if any(indicator in place_type for indicator in retail_indicators):
                return '5999'  # Miscellaneous Retail
        
        return None
    
    def _foursquare_categories_to_mcc(self, categories: List[dict]) -> Optional[str]:
        """Convert Foursquare categories to Stripe Issuing MCC categories"""
        if not categories:
            return None
        
        # Complete mapping using ALL official Stripe Issuing MCC codes
        category_patterns = {
            # Food & Dining
            ('restaurant', 'eating', 'dining', 'food', 'eatery', 'kitchen'): '5812',  # Eating Places, Restaurants
            ('fast food', 'quick service', 'fast casual', 'drive through', 'takeaway'): '5814',  # Fast Food Restaurants
            ('bakery', 'cafe', 'coffee', 'pastry', 'patisserie', 'tea'): '5462',  # Bakeries
            ('bar', 'pub', 'brewery', 'nightclub', 'cocktail', 'wine bar', 'liquor', 'distillery'): '5921',  # Package Stores-Beer, Wine, and Liquor
            ('caterer', 'catering', 'event catering'): '5811',  # Caterers
            
            # Agriculture & Farming
            ('farm', 'agriculture', 'agricultural', 'farming', 'ranch'): '0763',  # Agricultural Cooperative
            ('veterinary', 'animal hospital', 'pet clinic', 'vet'): '0742',  # Veterinary Services
            ('landscaping', 'lawn care', 'garden service', 'groundskeeping'): '0780',  # Landscaping Services
            
            # Construction & Contractors - Complete Coverage
            ('general contractor', 'construction', 'builder', 'building contractor'): '1520',  # General Contractors
            ('carpentry', 'carpenter', 'woodwork', 'cabinet'): '1750',  # Carpentry Services
            ('concrete', 'cement', 'masonry', 'stonework'): '1771',  # Concrete Work Services
            ('electrical', 'electrician', 'electric', 'wiring'): '1731',  # Electrical Contractors
            ('glass', 'glazing', 'window installation'): '1740',  # Masonry, Stonework, and Plaster
            ('heating', 'hvac', 'air conditioning', 'cooling', 'ventilation'): '1711',  # Plumbing, Heating, Air-Conditioning
            ('insulation', 'weatherproofing'): '1799',  # Special Trade Contractors
            ('painting', 'painter', 'decorating', 'wallpaper'): '1721',  # Painting, Paperhanging, Decorating
            ('plumbing', 'plumber', 'pipe', 'drainage'): '1711',  # Plumbing, Heating, Air-Conditioning
            ('roofing', 'roofer', 'siding', 'gutters'): '1761',  # Roofing/Siding, Sheet Metal
            ('welding', 'welder', 'metal fabrication'): '7692',  # Welding Repair
            
            # Manufacturing & Wholesale - Complete Coverage
            ('chemical', 'industrial', 'chemicals', 'laboratory supply'): '5169',  # Chemicals and Allied Products
            ('commercial equipment', 'industrial equipment'): '5046',  # Commercial Equipment
            ('computer wholesale', 'tech wholesale', 'electronics wholesale'): '5045',  # Computers, Peripherals, and Software
            ('construction materials', 'building materials wholesale'): '5039',  # Construction Materials
            ('drug wholesale', 'pharmaceutical wholesale', 'medical wholesale'): '5122',  # Drugs, Drug Proprietaries, and Druggist Sundries
            ('electrical parts', 'electrical wholesale'): '5065',  # Electrical Parts and Equipment
            ('footwear wholesale', 'shoe wholesale'): '5139',  # Commercial Footwear
            ('furniture wholesale', 'office furniture wholesale'): '5021',  # Office and Commercial Furniture
            ('hardware wholesale', 'tools wholesale'): '5072',  # Hardware, Equipment, and Supplies
            ('jewelry wholesale', 'watch wholesale'): '5094',  # Precious Stones and Metals, Watches and Jewelry
            ('lumber', 'building supplies', 'timber'): '5211',  # Lumber, Building Materials Stores
            ('metals', 'steel', 'metal service'): '5051',  # Metal Service Centers
            ('office supplies wholesale', 'stationery wholesale'): '5111',  # Stationery, Office Supplies, Printing and Writing Paper
            ('paint wholesale', 'coating wholesale'): '5198',  # Paints, Varnishes, and Supplies
            ('paper', 'paper products', 'packaging materials'): '5111',  # Stationery, Office Supplies, Printing and Writing Paper
            ('petroleum wholesale', 'fuel wholesale'): '5172',  # Petroleum and Petroleum Products
            ('photographic wholesale', 'camera wholesale'): '5044',  # Photographic, Photocopy, Microfilm Equipment, and Supplies
            ('plumbing wholesale', 'heating wholesale'): '5074',  # Plumbing, Heating Equipment, and Supplies
            ('textile wholesale', 'fabric wholesale'): '5131',  # Piece Goods, Notions, and Other Dry Goods
            ('tobacco wholesale', 'cigarette wholesale'): '5194',  # Tobacco and Tobacco Products
            
            # Publishing & Media
            ('book wholesale', 'publishing', 'publisher'): '5192',  # Books, Periodicals, and Newspapers
            ('printing', 'typesetting', 'print shop'): '2791',  # Typesetting, Plate Making, and Related Services
            ('newspaper', 'magazine', 'periodical'): '5192',  # Books, Periodicals, and Newspapers
            
            # Retail - Complete Coverage
            ('gas station', 'petrol station', 'fuel station'): '5541',  # Service Stations
            ('automated fuel', 'self service fuel'): '5542',  # Automated Fuel Dispensers
            ('grocery', 'supermarket', 'market', 'food store'): '5411',  # Grocery Stores, Supermarkets
            ('convenience store', 'corner store', 'mini mart'): '5499',  # Miscellaneous Food Stores - Convenience Stores and Specialty Markets
            ('candy store', 'confectionery', 'sweets', 'chocolate'): '5441',  # Candy, Nut, and Confectionery Stores
            ('clothing store', 'apparel', 'fashion'): '5651',  # Family Clothing Stores
            ('mens clothing', 'menswear'): '5611',  # Men's and Boys' Clothing and Accessories Stores
            ('womens clothing', 'ladies wear'): '5621',  # Women's Ready-To-Wear Stores
            ('childrens clothing', 'kids clothes', 'baby clothes'): '5641',  # Children's and Infants' Wear Stores
            ('womens accessories', 'handbags', 'purses'): '5631',  # Women's Accessory and Specialty Shops
            ('sports apparel', 'athletic wear', 'sportswear'): '5655',  # Sports and Riding Apparel Stores
            ('uniform', 'work clothes'): '5137',  # Uniforms, Commercial Clothing
            ('shoe store', 'footwear', 'boots', 'sneakers'): '5661',  # Shoe Stores
            ('electronics store', 'computer store', 'tech store'): '5732',  # Electronics Stores
            ('computer software', 'software store'): '5734',  # Computer Software Stores
            ('record store', 'music store', 'vinyl'): '5735',  # Record Stores
            ('department store', 'retail chain'): '5311',  # Department Stores
            ('discount store', 'dollar store'): '5310',  # Discount Stores
            ('variety store', 'general store'): '5331',  # Variety Stores
            ('wholesale club', 'membership store'): '5300',  # Wholesale Clubs
            ('pharmacy', 'drugstore', 'chemist'): '5912',  # Drug Stores and Pharmacies
            ('furniture store', 'home furnishing'): '5712',  # Furniture, Home Furnishings, and Equipment Stores, Except Appliances
            ('home improvement', 'home depot', 'hardware superstore'): '5200',  # Home Supply Warehouse Stores
            ('appliance store', 'kitchen appliances'): '5722',  # Household Appliance Stores
            ('jewelry store', 'jeweler', 'watches'): '5944',  # Jewelry Stores, Watches, Clocks, and Silverware Stores
            ('book store', 'bookshop', 'library store'): '5942',  # Book Stores
            ('stationery store', 'office supply', 'school supplies'): '5943',  # Stationery Stores, Office, and School Supply Stores
            ('sporting goods', 'sports equipment', 'outdoor gear'): '5941',  # Sporting Goods Stores
            ('toy store', 'hobby shop', 'games'): '5945',  # Hobby, Toy, and Game Shops
            ('camera store', 'photography equipment'): '5946',  # Camera and Photographic Supply Stores
            ('gift shop', 'novelty', 'souvenir'): '5947',  # Gift, Card, Novelty, and Souvenir Shops
            ('fabric store', 'sewing', 'needlework'): '5949',  # Sewing, Needlework, Fabric, and Piece Goods Stores
            ('hardware store', 'tools', 'home repair'): '5251',  # Hardware Stores
            ('paint store', 'wallpaper', 'decorating supplies'): '5231',  # Glass, Paint, and Wallpaper Stores
            ('lumber yard', 'building materials'): '5211',  # Lumber, Building Materials Stores
            ('nursery', 'garden center', 'plants'): '5261',  # Nurseries, Lawn and Garden Supply Stores
            ('pet store', 'pet supplies', 'pet food'): '5995',  # Pet Shops, Pet Food, and Supplies
            ('florist', 'flower shop', 'flowers'): '5992',  # Florists
            ('bicycle shop', 'bike store', 'cycling'): '5940',  # Bicycle Shops
            ('motorcycle dealer', 'bike dealer', 'scooter'): '5571',  # Motorcycle Shops and Dealers
            ('boat dealer', 'marine', 'yacht'): '5551',  # Boat Dealers
            ('rv dealer', 'recreational vehicle', 'camper'): '5561',  # Recreational Vehicle Dealers
            ('snowmobile dealer', 'winter sports'): '5598',  # Snowmobile Dealers
            ('art gallery', 'art dealer', 'fine art'): '5971',  # Art Dealers and Galleries
            ('artist supply', 'craft store', 'art materials'): '5970',  # Artists Supply and Craft Shops
            ('antique shop', 'antiques', 'collectibles'): '5932',  # Antique Shops
            ('antique reproduction', 'replica'): '5937',  # Antique Reproductions
            ('used goods', 'secondhand', 'consignment'): '5931',  # Used Merchandise and Secondhand Stores
            ('pawn shop', 'pawnbroker'): '5933',  # Pawn Shops
            ('cigar store', 'tobacco shop', 'smoking'): '5993',  # Cigar Stores and Stands
            ('cosmetic store', 'beauty products', 'makeup'): '5977',  # Cosmetic Stores
            ('typewriter store', 'office machines'): '5978',  # Typewriter Stores
            ('wig shop', 'hair pieces', 'toupee'): '5698',  # Wig and Toupee Stores
            ('religious goods', 'church supplies'): '5973',  # Religious Goods Stores
            ('stamp and coin', 'collectible currency'): '5972',  # Stamp and Coin Stores
            ('orthopedic goods', 'prosthetic', 'medical devices'): '5976',  # Orthopedic Goods - Prosthetic Devices
            ('optical shop', 'eyeglasses', 'contacts'): '5976',  # Opticians, Eyeglasses
            ('tent and awning', 'outdoor shelter'): '5998',  # Tent and Awning Shops
            ('swimming pool sales', 'pool supplies'): '5996',  # Swimming Pools Sales
            ('miscellaneous retail', 'general retail'): '5999',  # Miscellaneous Retail
            
            # Automotive - Complete Coverage
            ('car dealer', 'auto dealer', 'vehicle sales'): '5511',  # Car and Truck Dealers (New & Used) Sales, Service, Repairs Parts and Leasing
            ('used car dealer', 'pre-owned vehicles'): '5521',  # Car and Truck Dealers (Used Only) Sales, Service, Repairs Parts and Leasing
            ('tire shop', 'tire store', 'wheels'): '5532',  # Automotive Tire Stores
            ('auto parts', 'car parts', 'automotive accessories'): '5533',  # Automotive Parts and Accessories Stores
            ('auto supply', 'automotive supply'): '5531',  # Auto and Home Supply Stores
            ('car rental', 'vehicle rental', 'rent a car'): '7512',  # Car Rental Agencies
            ('truck rental', 'van rental', 'moving truck'): '7513',  # Truck/Utility Trailer Rentals
            ('rv rental', 'camper rental'): '7519',  # Recreational Vehicle Rentals
            ('auto body shop', 'collision repair', 'dent repair'): '7531',  # Auto Body Repair Shops
            ('tire repair', 'tire service'): '7534',  # Tire Retreading and Repair
            ('auto paint shop', 'car painting'): '7535',  # Auto Paint Shops
            ('auto repair', 'car service', 'mechanic'): '7538',  # Auto Service Shops
            ('car wash', 'auto wash', 'detailing'): '7542',  # Car Washes
            ('towing service', 'roadside assistance'): '7549',  # Towing Services
            
            # Financial Services - Complete Coverage
            ('bank', 'atm', 'financial institution'): '6011',  # Automated Cash Disburse
            ('quasi cash', 'cash advance'): '6051',  # Quasi Cash - Merchant
            ('credit union', 'savings bank'): '6012',  # Financial Institutions
            ('credit reporting', 'credit bureau'): '7321',  # Credit Reporting Agencies
            ('collection agency', 'debt collection'): '7322',  # Collection Agencies
            ('debt counseling', 'financial counseling'): '7299',  # Miscellaneous Personal Services
            ('check cashing', 'money services'): '6051',  # Quasi Cash - Merchant
            ('money order', 'wire transfer'): '4829',  # Wires, Money Orders
            ('security broker', 'investment', 'stock broker'): '6211',  # Security Brokers/Dealers
            ('insurance', 'insurance agent', 'coverage'): '6300',  # Insurance Sales, Underwriting, and Premiums
            ('real estate', 'property management', 'realtor'): '6513',  # Real Estate Agents and Managers - Rentals
            
            # Lodging & Travel
            ('hotel', 'motel', 'resort', 'inn'): '7011',  # Hotels, Motels, and Resorts
            ('timeshare', 'vacation rental'): '7012',  # Timeshares
            ('campground', 'camping', 'rv park'): '7033',  # Trailer Parks, Campgrounds
            ('sporting camp', 'adventure camp'): '7032',  # Sporting/Recreation Camps
            ('travel agency', 'tour operator', 'travel service'): '4722',  # Travel Agencies, Tour Operators
            ('tui travel', 'vacation package'): '4723',  # TUI Travel - Germany
            
            # Health & Medical - Complete Coverage
            ('hospital', 'medical center', 'clinic', 'healthcare'): '8062',  # Hospitals
            ('doctor', 'physician', 'medical doctor'): '8011',  # Doctors of Medicine
            ('dentist', 'dental', 'orthodontist'): '8021',  # Dentists, Orthodontists
            ('osteopath', 'osteopathic'): '8031',  # Osteopaths
            ('chiropractor', 'chiropractic'): '8041',  # Chiropractors
            ('optometrist', 'eye doctor', 'ophthalmologist'): '8042',  # Optometrists, Ophthalmologist
            ('optician', 'eyeglasses', 'optical'): '8043',  # Opticians, Eyeglasses
            ('podiatrist', 'foot doctor', 'chiropodist'): '8049',  # Chiropodists, Podiatrists
            ('nursing home', 'personal care', 'elderly care'): '8050',  # Nursing/Personal Care
            ('ambulance',): '4119',  # Ambulance Services
            ('blood', 'lab'): '8071',  # Medical and Dental Laboratories
            ('mental health', 'psychiatrist', 'therapist'): '8031',  # Osteopaths
            
            # Beauty & Personal Care
            ('salon', 'spa', 'beauty', 'barber', 'hair'): '7230',  # Barber and Beauty Shops
            ('nail', 'manicure', 'pedicure'): '7230',  # Barber and Beauty Shops
            ('massage',): '7298',  # Health and Beauty Spas
            ('laundry', 'dry clean'): '7216',  # Dry Cleaners
            ('tailor', 'alteration'): '5697',  # Tailors, Alterations
            
            # Fitness & Recreation
            ('gym', 'fitness', 'health club', 'yoga'): '7997',  # Membership Clubs (Sports, Recreation, Athletic)
            ('pool', 'swimming'): '7997',  # Sports Clubs/Fields
            ('tennis', 'court'): '7997',  # Sports Clubs/Fields
            ('golf', 'country club'): '7997',  # Country Clubs
            ('bowling',): '7933',  # Bowling Alleys
            ('billiard', 'pool hall'): '7932',  # Billiard/Pool Establishments
            ('recreation', 'camp'): '7032',  # Sporting/Recreation Camps
            
            # Entertainment & Recreation
            ('movie', 'cinema', 'theater', 'theatre'): '7832',  # Motion Picture Theaters
            ('park', 'amusement'): '7996',  # Amusement Parks/Carnivals
            ('casino', 'gambling', 'gaming'): '7995',  # Betting/Casino Gambling
            ('arcade',): '7994',  # Video Game Arcades
            ('aquarium',): '7998',  # Aquariums
            ('zoo',): '7998',  # Aquariums (includes zoos)
            ('museum',): '7991',  # Tourist Attractions and Exhibits
            ('band', 'orchestra', 'music'): '7929',  # Bands, Orchestras
            ('ticket', 'event'): '7922',  # Theatrical Ticket Agencies
            
            # Transportation
            ('taxi', 'cab', 'uber', 'lyft'): '4121',  # Taxicabs/Limousines
            ('bus', 'transit'): '4131',  # Bus Lines
            ('train', 'railway'): '4112',  # Passenger Railways
            ('airline', 'airport'): '4511',  # Airlines, Air Carriers
            ('ferry', 'boat'): '4111',  # Commuter Transport, Ferries
            ('parking', 'garage'): '7523',  # Parking Lots, Garages
            ('toll', 'bridge'): '4784',  # Tolls/Bridge Fees
            
            # Professional Services
            ('lawyer', 'attorney', 'legal service'): '8111',  # Legal Services, Attorneys
            ('accountant', 'bookkeeping', 'tax service'): '8931',  # Accounting/Bookkeeping Services
            ('advertising', 'marketing', 'ad agency'): '7311',  # Advertising Services
            ('consultant', 'consulting', 'public relations'): '7392',  # Consulting, Public Relations
            ('courier', 'delivery'): '4215',  # Courier Services
            ('cleaning', 'maintenance'): '7349',  # Cleaning and Maintenance
            ('security',): '7382',  # Security and Commodity Brokers, Dealers, Exchanges, and Services
            ('photography', 'photographer'): '7221',  # Photographic Studios
            ('printing', 'copy'): '7338',  # Quick Copy, Repro, and Blueprint
            ('employment', 'staffing'): '7361',  # Employment/Temp Agencies
            ('architect', 'architectural', 'surveying'): '8911',  # Architectural/Surveying Services
            ('engineering',): '8911',  # Architectural/Surveying Services
            
            # Education
            ('university', 'college', 'higher education'): '8220',  # Colleges, Universities
            ('elementary', 'primary'): '8211',  # Elementary, Secondary Schools
            ('childcare', 'daycare'): '8351',  # Child Care Services
            ('driving school',): '8299',  # Schools and Educational Services - Not Elsewhere Classified
            ('dance', 'music lesson'): '8299',  # Schools and Educational Services - Not Elsewhere Classified
            ('vocational', 'trade school'): '8249',  # Vocational/Trade Schools
            
            # Government & Public Services
            ('post office', 'postal service'): '9402',  # Postal Services - Government Only
            ('courthouse', 'court'): '9211',  # Court Costs, Including Alimony and Child Support
            ('city hall', 'government'): '9399',  # Government Services (Not Elsewhere Classified)
            ('library',): '8231',  # Correspondence Schools
            ('police', 'fire department'): '9399',  # Government Services (Not Elsewhere Classified)
            ('dmv', 'motor vehicle'): '9399',  # Government Services (Not Elsewhere Classified)
            
            # Religious & Charitable
            ('church', 'mosque', 'synagogue', 'temple', 'religious'): '8661',  # Religious Organizations
            ('charity', 'charitable', 'fundraising'): '8398',  # Charitable and Social Service Organizations - Fundraising
            
            # Utilities & Communication
            ('utility', 'electric', 'water', 'gas'): '4900',  # Utilities
            ('telephone', 'telecom'): '4814',  # Telecommunication Services
            ('internet', 'cable'): '4899',  # Cable, Satellite, and Other Pay Television and Radio
            
            # Construction & Home Improvement
            ('contractor', 'construction'): '1799',  # Special Trade Contractors
            ('plumbing', 'plumber'): '1711',  # Plumbing, Heating, Air-Conditioning
            ('electrical', 'electrician'): '1731',  # Electrical Contractors
            ('roofing',): '1761',  # Roofing/Siding, Sheet Metal
            ('painting', 'painter'): '1721',  # Painting, Paperhanging, Decorating
            ('landscaping', 'lawn'): '0780',  # Landscaping Services
        }
        
        # Check all categories and their names
        for category in categories:
            category_name = category.get('name', '').lower()
            
            # Check each pattern group
            for patterns, mcc in category_patterns.items():
                if any(pattern in category_name for pattern in patterns):
                    return mcc
        
        # Default retail categories
        retail_indicators = ['store', 'shop', 'retail', 'market']
        for category in categories:
            category_name = category.get('name', '').lower()
            if any(indicator in category_name for indicator in retail_indicators):
                return '5999'  # Miscellaneous Retail
        
        return None
    
    def _analyze_google_commercial_indicators(self, business_types: Dict[str, int]) -> Dict[str, Any]:
        """Analyze commercial indicators from Google Places data"""
        commercial_types = [
            'store', 'restaurant', 'shopping_mall', 'bank', 'gas_station',
            'pharmacy', 'hospital', 'lodging', 'car_dealer'
        ]
        
        commercial_count = sum(count for btype, count in business_types.items() 
                             if any(ct in btype for ct in commercial_types))
        total_count = sum(business_types.values())
        
        return {
            'commercial_ratio': commercial_count / total_count if total_count > 0 else 0,
            'commercial_diversity': len([bt for bt in business_types.keys() 
                                       if any(ct in bt for ct in commercial_types)]),
            'is_commercial_area': commercial_count > total_count * 0.6
        }
    
    def _analyze_foursquare_commercial_indicators(self, categories: Dict[str, int]) -> Dict[str, Any]:
        """Analyze commercial indicators from Foursquare data"""
        commercial_keywords = [
            'shop', 'store', 'restaurant', 'cafe', 'bank', 'mall',
            'market', 'boutique', 'salon', 'spa', 'hotel'
        ]
        
        commercial_count = sum(count for cat, count in categories.items()
                             if any(kw in cat.lower() for kw in commercial_keywords))
        total_count = sum(categories.values())
        
        return {
            'commercial_ratio': commercial_count / total_count if total_count > 0 else 0,
            'venue_diversity': len(categories),
            'is_commercial_area': commercial_count > total_count * 0.7
        }
    
    def _categorize_density(self, score: float) -> str:
        """Categorize business density based on score"""
        if score >= 0.8:
            return "very_high"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def _calculate_location_precision(self, lat: float, lng: float) -> Dict[str, Any]:
        """Calculate location precision metrics"""
        # This would incorporate GPS accuracy, cell tower triangulation, etc.
        # For now, return basic precision categories
        return {
            'gps_precision': 'high',  # Assume high GPS precision
            'building_level': True,
            'street_level': True,
            'neighborhood_level': True
        }
    
    def _generate_location_cache_key(self, lat: float, lng: float, radius: int) -> str:
        """Generate cache key for location analysis"""
        # Round coordinates to reduce cache variations
        lat_rounded = round(lat, 4)  # ~11m precision
        lng_rounded = round(lng, 4)
        return f"location_{lat_rounded}_{lng_rounded}_{radius}"
    
    def _generate_location_hash(self, lat: float, lng: float, precision: int = 7) -> str:
        """Generate location hash using H3 hexagonal indexing"""
        try:
            return h3.geo_to_h3(lat, lng, precision)
        except:
            # Fallback to simple hash
            return hashlib.md5(f"{round(lat, 4)}_{round(lng, 4)}".encode()).hexdigest()[:10]
    
    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached location analysis"""
        try:
            if self.supabase:
                result = await self.supabase.table('location_cache').select('*').eq('cache_key', cache_key).execute()
                if result.data:
                    cache_entry = result.data[0]
                    cached_at = datetime.fromisoformat(cache_entry['created_at'].replace('Z', '+00:00'))
                    if datetime.now() - cached_at < self.cache_duration:
                        return json.loads(cache_entry['analysis_data'])
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {str(e)}")
        return None
    
    async def _cache_analysis(self, cache_key: str, analysis: Dict[str, Any]):
        """Cache location analysis"""
        try:
            if self.supabase:
                await self.supabase.table('location_cache').upsert({
                    'cache_key': cache_key,
                    'analysis_data': json.dumps(analysis),
                    'created_at': datetime.now().isoformat()
                }).execute()
        except Exception as e:
            logger.error(f"Error caching analysis: {str(e)}")
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Return fallback analysis when APIs fail"""
        return {
            'commercial_score': 0.3,
            'business_density': 'unknown',
            'primary_business_types': [],
            'predicted_mcc': {'mcc': '5999', 'confidence': 0.2, 'source': 'fallback'},
            'confidence_factors': {
                'google_api_available': False,
                'foursquare_api_available': False,
                'historical_data_available': False,
                'combined_business_count': 0
            }
        } 