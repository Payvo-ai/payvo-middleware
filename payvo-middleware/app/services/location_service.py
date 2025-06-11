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
from app.utils.mcc_categories import get_mcc_for_google_place_type, get_mcc_for_foursquare_category

logger = logging.getLogger(__name__)

class LocationService:
    """Enhanced location service with real API integrations"""
    
    def __init__(self):
        self.google_maps_client = None
        self.foursquare_api_key = None
        self.cache_duration = timedelta(hours=6)  # Cache results for 6 hours
        self.supabase = None
        
    async def initialize(self):
        """Initialize the location service with database connectivity"""
        try:
            # Initialize Supabase client (synchronous call, no await needed)
            self.supabase = get_supabase_client()
            
            # Test database connectivity if available
            if self.supabase.is_available:
                # Supabase operations are synchronous, no await needed
                self.supabase.client.table('business_locations').select('*').limit(1).execute()
                logger.info("Location service database connectivity verified")
            else:
                logger.warning("Location service: Supabase not available, using in-memory fallback")
                
        except Exception as e:
            logger.warning(f"Location service database connection failed: {e}")
            self.supabase = None
    
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
            logger.warning("Google Maps client not initialized - no Google Places data available")
            return {"businesses": [], "density_score": 0.0}
        
        try:
            logger.info(f"Searching Google Places at ({lat}, {lng}) within {radius}m radius")
            
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
            
            logger.info(f"Google Places API returned {len(places_result.get('results', []))} places")
            
            for place in places_result.get('results', []):
                place_types = place.get('types', [])
                rating = place.get('rating', 0)
                place_name = place.get('name', 'Unknown')
                
                # Get MCC category for this place
                mcc_category = self._google_types_to_mcc_category(place_types)
                
                # Extract business info
                business = {
                    'name': place_name,
                    'types': place_types,
                    'rating': rating,
                    'price_level': place.get('price_level', 0),
                    'place_id': place.get('place_id', ''),
                    'location': place.get('geometry', {}).get('location', {}),
                    'mcc_category': mcc_category
                }
                businesses.append(business)
                
                logger.debug(f"Google Places: {place_name} | Types: {place_types} | MCC: {mcc_category}")
                
                # Count business types
                for business_type in place_types:
                    if business_type not in ['establishment', 'point_of_interest']:
                        business_types[business_type] = business_types.get(business_type, 0) + 1
                
                # Calculate average rating
                if rating > 0:
                    total_rating_sum += rating
                    rated_businesses += 1
            
            avg_rating = total_rating_sum / rated_businesses if rated_businesses > 0 else 0
            
            # Count how many businesses have specific MCC categories
            specific_mcc_count = sum(1 for b in businesses if b.get('mcc_category') and b.get('mcc_category') != '5999')
            logger.info(f"Google Places: {len(businesses)} total businesses, {specific_mcc_count} with specific MCC mappings")
            
            result = {
                'businesses': businesses,
                'business_count': len(businesses),
                'business_types': business_types,
                'density_score': min(len(businesses) / 50.0, 1.0),  # Normalize to 0-1
                'average_rating': avg_rating,
                'commercial_indicators': self._analyze_google_commercial_indicators(business_types)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Google Places data: {str(e)}")
            return {"businesses": [], "density_score": 0.0}
    
    async def _get_foursquare_data(self, lat: float, lng: float, radius: int) -> Dict[str, Any]:
        """Get venue data from Foursquare API"""
        if not self.foursquare_api_key:
            logger.warning("Foursquare API key not found - no Foursquare data available")
            return {"venues": [], "density_score": 0.0}
        
        try:
            logger.info(f"Searching Foursquare venues at ({lat}, {lng}) within {radius}m radius")
            
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
                
                logger.info(f"Foursquare API returned {len(data.get('results', []))} venues")
                
                for venue in data.get('results', []):
                    venue_categories = venue.get('categories', [])
                    venue_name = venue.get('name', 'Unknown')
                    
                    # Get MCC category for this venue
                    mcc_category = self._foursquare_categories_to_mcc(venue_categories)
                    
                    venue_info = {
                        'name': venue_name,
                        'categories': [cat.get('name', '') for cat in venue_categories],
                        'rating': venue.get('rating', 0),
                        'price': venue.get('price', 0),
                        'location': venue.get('location', {}),
                        'stats': venue.get('stats', {}),
                        'mcc_category': mcc_category
                    }
                    venues.append(venue_info)
                    
                    category_names = [cat.get('name', '') for cat in venue_categories]
                    logger.debug(f"Foursquare: {venue_name} | Categories: {category_names} | MCC: {mcc_category}")
                    
                    # Count categories
                    for cat in venue_categories:
                        cat_name = cat.get('name', '')
                        categories[cat_name] = categories.get(cat_name, 0) + 1
                
                # Count how many venues have specific MCC categories
                specific_mcc_count = sum(1 for v in venues if v.get('mcc_category') and v.get('mcc_category') != '5999')
                logger.info(f"Foursquare: {len(venues)} total venues, {specific_mcc_count} with specific MCC mappings")
                
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
            if self.supabase and self.supabase.is_available:
                # Supabase operations are synchronous
                result = self.supabase.client.table('transaction_history').select(
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
        mcc_scores = {}
        total_businesses = 0
        
        # Google Places analysis
        for business in google_data.get('businesses', []):
            mcc_code = business.get('mcc_category')
            if mcc_code and mcc_code != "5999":  # Only count specific MCC matches
                weight = business.get('rating', 3.0) / 5.0  # Normalize rating
                mcc_scores[mcc_code] = mcc_scores.get(mcc_code, 0) + weight
                total_businesses += 1
                logger.debug(f"Google Places business: {business.get('name', 'Unknown')} -> MCC {mcc_code} (weight: {weight:.2f})")
        
        # Foursquare analysis
        for venue in foursquare_data.get('venues', []):
            mcc_code = venue.get('mcc_category')
            if mcc_code and mcc_code != "5999":  # Only count specific MCC matches
                weight = venue.get('rating', 6.0) / 10.0  # Normalize rating
                mcc_scores[mcc_code] = mcc_scores.get(mcc_code, 0) + weight
                total_businesses += 1
                logger.debug(f"Foursquare venue: {venue.get('name', 'Unknown')} -> MCC {mcc_code} (weight: {weight:.2f})")
        
        logger.info(f"Combined MCC analysis: {len(mcc_scores)} unique MCCs from {total_businesses} businesses")
        logger.info(f"MCC scores: {mcc_scores}")
        
        if mcc_scores:
            # Find the MCC with highest score
            best_mcc = max(mcc_scores, key=mcc_scores.get)
            best_score = mcc_scores[best_mcc]
            total_score = sum(mcc_scores.values())
            
            # Calculate confidence based on consensus and data quality
            base_confidence = best_score / total_score if total_score > 0 else 0
            business_count_bonus = min(0.2, total_businesses * 0.05)  # Bonus for more data
            consensus_bonus = min(0.1, (len(mcc_scores) - 1) * 0.02)  # Bonus for multiple sources
            
            final_confidence = min(0.9, base_confidence + business_count_bonus + consensus_bonus)
            
            logger.info(f"Best MCC prediction: {best_mcc} with confidence {final_confidence:.2f}")
            
            return {
                'mcc': best_mcc,
                'confidence': final_confidence,
                'source': 'combined_apis',
                'details': {
                    'mcc_scores': mcc_scores,
                    'total_businesses': total_businesses,
                    'google_count': google_data.get('business_count', 0),
                    'foursquare_count': foursquare_data.get('venue_count', 0)
                }
            }
        
        # Log why we're falling back
        logger.warning(f"No specific MCC predictions found. Google businesses: {google_data.get('business_count', 0)}, Foursquare venues: {foursquare_data.get('venue_count', 0)}")
        
        # Fallback
        return {
            'mcc': '5999',
            'confidence': 0.3,
            'source': 'fallback',
            'details': {
                'reason': 'no_specific_predictions',
                'google_count': google_data.get('business_count', 0),
                'foursquare_count': foursquare_data.get('venue_count', 0)
            }
        }
    
    def _google_types_to_mcc_category(self, types: List[str]) -> Optional[str]:
        """Enhanced Google Places types to MCC mapping using centralized utility"""
        for place_type in types:
            mcc = get_mcc_for_google_place_type(place_type)
            if mcc and mcc != "5999":  # Found a specific match
                return mcc
        
        # Return fallback if no specific match found
        return "5999"
    
    def _foursquare_categories_to_mcc(self, categories: List[Dict]) -> Optional[str]:
        """Enhanced Foursquare category to MCC mapping using centralized utility"""
        for category in categories:
            category_name = category.get('name', '')
            if category_name:
                mcc = get_mcc_for_foursquare_category(category_name)
                if mcc and mcc != "5999":  # Found a specific match
                    return mcc
        
        # Return fallback if no specific match found
        return "5999"
    
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
            if self.supabase and self.supabase.is_available:
                # Supabase operations are synchronous
                result = self.supabase.client.table('location_cache').select('*').eq('cache_key', cache_key).execute()
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
            if self.supabase and self.supabase.is_available:
                # Supabase operations are synchronous
                self.supabase.client.table('location_cache').upsert({
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