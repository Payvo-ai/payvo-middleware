"""
Enhanced Historical Data Service for MCC Prediction
Provides comprehensive area-based transaction pattern analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np
from geopy.distance import geodesic
import h3

from ..core.config import settings
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class HistoricalService:
    """Enhanced historical transaction analysis service"""
    
    def __init__(self):
        self.supabase = None
        self.area_cache = {}
        self.pattern_cache = {}
        self.cache_duration = timedelta(hours=6)  # Cache area data for 6 hours
        self.h3_resolution = 9  # ~50m hexagons for precise area analysis
        
    async def initialize(self):
        """Initialize the historical service with database connectivity"""
        try:
            # Initialize Supabase client (synchronous call, no await needed)
            self.supabase = get_supabase_client()
            
            # Test database connectivity if available
            if self.supabase.is_available:
                # Test all required tables
                await self.supabase.table('transaction_history').select('*').limit(1).execute()
                await self.supabase.table('area_patterns').select('*').limit(1).execute()
                await self.supabase.table('merchant_locations').select('*').limit(1).execute()
                logger.info("Historical service database connectivity verified")
            else:
                logger.warning("Historical service: Supabase not available, using in-memory fallback")
                
        except Exception as e:
            logger.warning(f"Historical service database connection failed: {e}")
            self.supabase = None
    
    async def analyze_area_patterns(self, latitude: float, longitude: float, 
                                  radius_meters: int = 200,
                                  transaction_amount: Optional[float] = None,
                                  transaction_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyze historical transaction patterns for a specific area
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude  
            radius_meters: Analysis radius in meters
            transaction_amount: Optional current transaction amount
            transaction_time: Optional current transaction time
        
        Returns:
            Comprehensive area analysis with MCC predictions
        """
        try:
            # Generate H3 hex ID for the location
            h3_hex = h3.geo_to_h3(latitude, longitude, self.h3_resolution)
            
            # Check cache first
            cache_key = f"{h3_hex}_{radius_meters}"
            cached_result = await self._get_cached_area_analysis(cache_key)
            if cached_result and self._is_cache_valid(cached_result):
                return self._enhance_cached_analysis(
                    cached_result, transaction_amount, transaction_time
                )
            
            # Perform comprehensive historical analysis
            transaction_analysis = await self._analyze_area_transactions(
                latitude, longitude, radius_meters
            )
            
            merchant_analysis = await self._analyze_area_merchants(
                latitude, longitude, radius_meters
            )
            
            temporal_analysis = await self._analyze_temporal_patterns(
                latitude, longitude, radius_meters, transaction_time
            )
            
            behavioral_analysis = await self._analyze_behavioral_patterns(
                latitude, longitude, radius_meters, transaction_amount, transaction_time
            )
            
            density_analysis = await self._analyze_transaction_density(
                latitude, longitude, radius_meters
            )
            
            # Combine all analyses
            combined_analysis = self._combine_historical_analyses(
                transaction_analysis, merchant_analysis, temporal_analysis,
                behavioral_analysis, density_analysis, latitude, longitude
            )
            
            # Cache the result
            await self._cache_area_analysis(cache_key, combined_analysis)
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing area patterns: {str(e)}")
            return self._get_empty_analysis_result()
    
    async def _analyze_area_transactions(self, lat: float, lon: float, 
                                       radius_meters: int) -> Dict[str, Any]:
        """Analyze transaction history in the specified area"""
        try:
            if not self.supabase:
                return {'analyzed': False, 'reason': 'no_database'}
            
            # Query transactions within the area (last 6 months)
            cutoff_date = (datetime.now() - timedelta(days=180)).isoformat()
            
            # Use PostGIS ST_DWithin for spatial query
            result = await self.supabase.rpc('get_transactions_within_radius', {
                'center_lat': lat,
                'center_lon': lon,
                'radius_meters': radius_meters,
                'since_date': cutoff_date
            }).execute()
            
            if not result.data or len(result.data) < 10:
                return {
                    'analyzed': False,
                    'reason': 'insufficient_data',
                    'transaction_count': len(result.data) if result.data else 0
                }
            
            transactions = result.data
            
            # Analyze transaction patterns
            amounts = [float(t['amount']) for t in transactions if t.get('amount')]
            mccs = [t['mcc'] for t in transactions if t.get('mcc')]
            merchants = [t['merchant_name'] for t in transactions if t.get('merchant_name')]
            success_rates = [t['success'] for t in transactions if 'success' in t]
            
            # Calculate MCC distribution and confidence
            mcc_counts = Counter(mccs)
            total_transactions = len(mccs)
            
            mcc_distribution = {}
            for mcc, count in mcc_counts.items():
                percentage = count / total_transactions
                mcc_distribution[mcc] = {
                    'count': count,
                    'percentage': percentage,
                    'confidence': min(0.9, percentage + 0.1)  # Base confidence on frequency
                }
            
            # Determine dominant MCC
            dominant_mcc = None
            dominant_confidence = 0.0
            if mcc_counts:
                dominant_mcc, dominant_count = mcc_counts.most_common(1)[0]
                dominant_percentage = dominant_count / total_transactions
                dominant_confidence = min(0.9, dominant_percentage + 0.2)
            
            return {
                'analyzed': True,
                'transaction_count': len(transactions),
                'date_range': {
                    'earliest': min([t['transaction_time'] for t in transactions]),
                    'latest': max([t['transaction_time'] for t in transactions])
                },
                'amount_statistics': {
                    'avg': np.mean(amounts) if amounts else 0,
                    'median': np.median(amounts) if amounts else 0,
                    'std': np.std(amounts) if amounts else 0,
                    'total': sum(amounts) if amounts else 0
                },
                'mcc_analysis': {
                    'distribution': mcc_distribution,
                    'dominant_mcc': dominant_mcc,
                    'dominant_confidence': dominant_confidence,
                    'mcc_diversity': len(mcc_counts),
                    'entropy': self._calculate_mcc_entropy(mcc_counts)
                },
                'merchant_analysis': {
                    'unique_merchants': len(set(merchants)),
                    'merchant_frequency': dict(Counter(merchants)),
                    'top_merchants': Counter(merchants).most_common(5)
                },
                'success_analysis': {
                    'success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
                    'total_attempts': len(success_rates)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing area transactions: {str(e)}")
            return {'analyzed': False, 'reason': 'analysis_error'}
    
    async def _analyze_area_merchants(self, lat: float, lon: float, 
                                    radius_meters: int) -> Dict[str, Any]:
        """Analyze known merchants in the specified area"""
        try:
            if not self.supabase:
                return {'analyzed': False}
            
            # Query merchant locations within the area
            result = await self.supabase.rpc('get_merchants_within_radius', {
                'center_lat': lat,
                'center_lon': lon,
                'radius_meters': radius_meters
            }).execute()
            
            if not result.data:
                return {'analyzed': False, 'reason': 'no_merchants_found'}
            
            merchants = result.data
            
            # Analyze merchant categories
            merchant_mccs = [m['mcc'] for m in merchants if m.get('mcc')]
            merchant_categories = [m['category'] for m in merchants if m.get('category')]
            
            # Calculate category distribution
            mcc_distribution = Counter(merchant_mccs)
            category_distribution = Counter(merchant_categories)
            
            # Calculate confidence based on merchant consistency
            total_merchants = len(merchants)
            mcc_consistency = {}
            
            for mcc, count in mcc_distribution.items():
                percentage = count / total_merchants
                mcc_consistency[mcc] = {
                    'merchant_count': count,
                    'percentage': percentage,
                    'confidence': min(0.8, percentage + 0.3)  # Higher confidence for merchant data
                }
            
            # Find dominant merchant type
            dominant_mcc = None
            dominant_confidence = 0.0
            if mcc_distribution:
                dominant_mcc, dominant_count = mcc_distribution.most_common(1)[0]
                dominant_percentage = dominant_count / total_merchants
                dominant_confidence = min(0.85, dominant_percentage + 0.35)
            
            return {
                'analyzed': True,
                'merchant_count': total_merchants,
                'merchant_details': merchants,
                'mcc_analysis': {
                    'distribution': dict(mcc_distribution),
                    'consistency': mcc_consistency,
                    'dominant_mcc': dominant_mcc,
                    'dominant_confidence': dominant_confidence
                },
                'category_analysis': {
                    'distribution': dict(category_distribution),
                    'diversity': len(category_distribution)
                },
                'area_characteristics': {
                    'merchant_density': total_merchants / (np.pi * (radius_meters/1000)**2),  # per km²
                    'category_diversity': len(category_distribution),
                    'avg_distance_from_center': np.mean([
                        geodesic((lat, lon), (m['latitude'], m['longitude'])).meters 
                        for m in merchants if m.get('latitude') and m.get('longitude')
                    ]) if merchants else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing area merchants: {str(e)}")
            return {'analyzed': False, 'reason': 'analysis_error'}
    
    async def _analyze_temporal_patterns(self, lat: float, lon: float, 
                                       radius_meters: int,
                                       current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze temporal transaction patterns in the area"""
        try:
            if not self.supabase:
                return {'analyzed': False}
            
            # Query temporal transaction patterns
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            result = await self.supabase.rpc('get_temporal_patterns_within_radius', {
                'center_lat': lat,
                'center_lon': lon,
                'radius_meters': radius_meters,
                'since_date': cutoff_date
            }).execute()
            
            if not result.data:
                return {'analyzed': False, 'reason': 'no_temporal_data'}
            
            transactions = result.data
            
            # Extract temporal features
            hours = []
            days_of_week = []
            mccs_by_hour = defaultdict(list)
            mccs_by_day = defaultdict(list)
            
            for t in transactions:
                if t.get('transaction_time') and t.get('mcc'):
                    dt = datetime.fromisoformat(t['transaction_time'].replace('Z', '+00:00'))
                    hour = dt.hour
                    day_of_week = dt.weekday()
                    
                    hours.append(hour)
                    days_of_week.append(day_of_week)
                    mccs_by_hour[hour].append(t['mcc'])
                    mccs_by_day[day_of_week].append(t['mcc'])
            
            # Analyze patterns
            hour_distribution = Counter(hours)
            day_distribution = Counter(days_of_week)
            
            # Find peak times for different MCCs
            peak_hours_by_mcc = {}
            for hour, mcc_list in mccs_by_hour.items():
                mcc_counts = Counter(mcc_list)
                for mcc, count in mcc_counts.items():
                    if mcc not in peak_hours_by_mcc:
                        peak_hours_by_mcc[mcc] = []
                    peak_hours_by_mcc[mcc].append({'hour': hour, 'count': count})
            
            # Sort peak hours for each MCC
            for mcc in peak_hours_by_mcc:
                peak_hours_by_mcc[mcc].sort(key=lambda x: x['count'], reverse=True)
                peak_hours_by_mcc[mcc] = peak_hours_by_mcc[mcc][:3]  # Top 3 peak hours
            
            # Current time analysis
            current_time_analysis = {}
            if current_time:
                current_hour = current_time.hour
                current_day = current_time.weekday()
                
                # Find MCCs most active at current time
                current_hour_mccs = Counter(mccs_by_hour.get(current_hour, []))
                current_day_mccs = Counter(mccs_by_day.get(current_day, []))
                
                if current_hour_mccs:
                    most_likely_mcc, count = current_hour_mccs.most_common(1)[0]
                    total_current_hour = sum(current_hour_mccs.values())
                    confidence = min(0.8, count / total_current_hour + 0.2)
                    
                    current_time_analysis = {
                        'predicted_mcc': most_likely_mcc,
                        'confidence': confidence,
                        'basis': 'current_hour_pattern',
                        'supporting_transactions': count
                    }
            
            return {
                'analyzed': True,
                'total_transactions': len(transactions),
                'temporal_distribution': {
                    'hourly': dict(hour_distribution),
                    'daily': dict(day_distribution)
                },
                'peak_patterns': {
                    'peak_hours': [h for h, c in hour_distribution.most_common(3)],
                    'peak_days': [d for d, c in day_distribution.most_common(3)],
                    'mcc_peak_hours': peak_hours_by_mcc
                },
                'current_time_analysis': current_time_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal patterns: {str(e)}")
            return {'analyzed': False, 'reason': 'analysis_error'}
    
    async def _analyze_behavioral_patterns(self, lat: float, lon: float, 
                                         radius_meters: int,
                                         current_amount: Optional[float] = None,
                                         current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze behavioral transaction patterns in the area"""
        try:
            if not self.supabase:
                return {'analyzed': False}
            
            # Query behavioral patterns
            cutoff_date = (datetime.now() - timedelta(days=60)).isoformat()
            
            result = await self.supabase.rpc('get_behavioral_patterns_within_radius', {
                'center_lat': lat,
                'center_lon': lon,
                'radius_meters': radius_meters,
                'since_date': cutoff_date
            }).execute()
            
            if not result.data:
                return {'analyzed': False, 'reason': 'no_behavioral_data'}
            
            transactions = result.data
            
            # Group transactions by MCC for behavioral analysis
            mcc_behaviors = defaultdict(list)
            for t in transactions:
                if t.get('mcc') and t.get('amount'):
                    mcc_behaviors[t['mcc']].append({
                        'amount': float(t['amount']),
                        'time': t.get('transaction_time'),
                        'success': t.get('success', True),
                        'card_type': t.get('card_type'),
                        'has_tip': t.get('has_tip', False)
                    })
            
            # Analyze each MCC's behavioral patterns
            behavioral_analysis = {}
            for mcc, mcc_transactions in mcc_behaviors.items():
                amounts = [t['amount'] for t in mcc_transactions]
                tips = [t['has_tip'] for t in mcc_transactions]
                success_rates = [t['success'] for t in mcc_transactions]
                
                behavioral_analysis[mcc] = {
                    'transaction_count': len(mcc_transactions),
                    'amount_patterns': {
                        'avg': np.mean(amounts),
                        'median': np.median(amounts),
                        'std': np.std(amounts),
                        'range': [min(amounts), max(amounts)]
                    },
                    'behavioral_indicators': {
                        'tip_frequency': sum(tips) / len(tips) if tips else 0,
                        'success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
                        'amount_consistency': 1.0 / (1.0 + np.std(amounts) / np.mean(amounts)) if amounts else 0
                    }
                }
            
            # Current transaction analysis
            current_transaction_analysis = {}
            if current_amount and current_time:
                current_hour = current_time.hour
                is_weekend = current_time.weekday() >= 5
                
                # Find MCCs with similar transaction patterns
                matching_mccs = []
                for mcc, patterns in behavioral_analysis.items():
                    amount_avg = patterns['amount_patterns']['avg']
                    amount_std = patterns['amount_patterns']['std']
                    
                    # Check if current amount fits the pattern
                    if amount_avg - 2*amount_std <= current_amount <= amount_avg + 2*amount_std:
                        # Calculate similarity score
                        amount_similarity = 1.0 - abs(current_amount - amount_avg) / (amount_avg + 1)
                        
                        matching_mccs.append({
                            'mcc': mcc,
                            'similarity_score': amount_similarity,
                            'confidence': min(0.8, amount_similarity * patterns['transaction_count'] / 100),
                            'supporting_transactions': patterns['transaction_count']
                        })
                
                # Sort by similarity and confidence
                matching_mccs.sort(key=lambda x: x['confidence'], reverse=True)
                
                if matching_mccs:
                    current_transaction_analysis = {
                        'best_match': matching_mccs[0],
                        'all_matches': matching_mccs[:5],  # Top 5 matches
                        'basis': 'amount_behavioral_pattern'
                    }
            
            return {
                'analyzed': True,
                'mcc_count': len(behavioral_analysis),
                'behavioral_patterns': behavioral_analysis,
                'current_transaction_analysis': current_transaction_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {str(e)}")
            return {'analyzed': False, 'reason': 'analysis_error'}
    
    async def _analyze_transaction_density(self, lat: float, lon: float, 
                                         radius_meters: int) -> Dict[str, Any]:
        """Analyze transaction density and distribution in the area"""
        try:
            if not self.supabase:
                return {'analyzed': False}
            
            # Get H3 hexagons around the center point
            center_hex = h3.geo_to_h3(lat, lon, self.h3_resolution)
            surrounding_hexes = h3.k_ring(center_hex, 2)  # Include surrounding hexagons
            
            # Query transaction density for each hex
            hex_data = {}
            for hex_id in surrounding_hexes:
                hex_center = h3.h3_to_geo(hex_id)
                
                result = await self.supabase.rpc('get_hex_transaction_summary', {
                    'hex_id': hex_id,
                    'center_lat': hex_center[0],
                    'center_lon': hex_center[1],
                    'days_back': 30
                }).execute()
                
                if result.data:
                    hex_data[hex_id] = result.data[0]
            
            # Calculate density metrics
            total_transactions = sum([h.get('transaction_count', 0) for h in hex_data.values()])
            total_area_km2 = len(hex_data) * 0.002  # Approximate area per hex at resolution 9
            
            density_analysis = {
                'analyzed': True,
                'center_hex': center_hex,
                'analyzed_hexes': len(hex_data),
                'total_transactions': total_transactions,
                'density_per_km2': total_transactions / total_area_km2 if total_area_km2 > 0 else 0,
                'hex_details': hex_data
            }
            
            # Find the most active hex and its dominant MCC
            if hex_data:
                most_active_hex = max(hex_data.keys(), 
                                    key=lambda h: hex_data[h].get('transaction_count', 0))
                most_active_data = hex_data[most_active_hex]
                
                density_analysis.update({
                    'most_active_hex': most_active_hex,
                    'most_active_mcc': most_active_data.get('dominant_mcc'),
                    'activity_confidence': min(0.7, most_active_data.get('transaction_count', 0) / 100)
                })
            
            return density_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing transaction density: {str(e)}")
            return {'analyzed': False, 'reason': 'analysis_error'}
    
    def _combine_historical_analyses(self, transaction_analysis: Dict, merchant_analysis: Dict,
                                   temporal_analysis: Dict, behavioral_analysis: Dict,
                                   density_analysis: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Combine all historical analysis results"""
        
        predictions = []
        confidence_factors = {}
        
        # Transaction history prediction (highest weight)
        if transaction_analysis.get('analyzed') and transaction_analysis.get('mcc_analysis', {}).get('dominant_mcc'):
            mcc_data = transaction_analysis['mcc_analysis']
            predictions.append({
                'mcc': mcc_data['dominant_mcc'],
                'confidence': mcc_data['dominant_confidence'],
                'method': 'historical_transaction_analysis',
                'weight': 0.4,
                'supporting_data': {
                    'transaction_count': transaction_analysis['transaction_count'],
                    'mcc_percentage': mcc_data.get('distribution', {}).get(mcc_data['dominant_mcc'], {}).get('percentage', 0)
                }
            })
            confidence_factors['transaction_history'] = True
        
        # Merchant location prediction (high weight)
        if merchant_analysis.get('analyzed') and merchant_analysis.get('mcc_analysis', {}).get('dominant_mcc'):
            mcc_data = merchant_analysis['mcc_analysis']
            predictions.append({
                'mcc': mcc_data['dominant_mcc'],
                'confidence': mcc_data['dominant_confidence'],
                'method': 'merchant_location_analysis',
                'weight': 0.3,
                'supporting_data': {
                    'merchant_count': merchant_analysis['merchant_count'],
                    'merchant_percentage': mcc_data.get('consistency', {}).get(mcc_data['dominant_mcc'], {}).get('percentage', 0)
                }
            })
            confidence_factors['merchant_data'] = True
        
        # Temporal pattern prediction (medium weight)
        if temporal_analysis.get('analyzed') and temporal_analysis.get('current_time_analysis', {}).get('predicted_mcc'):
            temporal_data = temporal_analysis['current_time_analysis']
            predictions.append({
                'mcc': temporal_data['predicted_mcc'],
                'confidence': temporal_data['confidence'],
                'method': 'temporal_pattern_analysis',
                'weight': 0.2,
                'supporting_data': {
                    'supporting_transactions': temporal_data['supporting_transactions'],
                    'basis': temporal_data['basis']
                }
            })
            confidence_factors['temporal_patterns'] = True
        
        # Behavioral pattern prediction (medium weight)
        if behavioral_analysis.get('analyzed') and behavioral_analysis.get('current_transaction_analysis', {}).get('best_match'):
            behavioral_data = behavioral_analysis['current_transaction_analysis']['best_match']
            predictions.append({
                'mcc': behavioral_data['mcc'],
                'confidence': behavioral_data['confidence'],
                'method': 'behavioral_pattern_analysis',
                'weight': 0.1,
                'supporting_data': {
                    'similarity_score': behavioral_data['similarity_score'],
                    'supporting_transactions': behavioral_data['supporting_transactions']
                }
            })
            confidence_factors['behavioral_patterns'] = True
        
        # Calculate weighted final prediction
        if predictions:
            # Normalize weights
            total_weight = sum([p['weight'] for p in predictions])
            for pred in predictions:
                pred['normalized_weight'] = pred['weight'] / total_weight
            
            # Group predictions by MCC and calculate weighted confidence
            mcc_scores = defaultdict(list)
            for pred in predictions:
                mcc_scores[pred['mcc']].append({
                    'confidence': pred['confidence'],
                    'weight': pred['normalized_weight'],
                    'method': pred['method']
                })
            
            # Calculate final scores for each MCC
            final_predictions = []
            for mcc, scores in mcc_scores.items():
                weighted_confidence = sum([s['confidence'] * s['weight'] for s in scores])
                total_weight = sum([s['weight'] for s in scores])
                methods = [s['method'] for s in scores]
                
                final_predictions.append({
                    'mcc': mcc,
                    'confidence': weighted_confidence,
                    'weight': total_weight,
                    'methods': methods
                })
            
            # Select best prediction
            best_prediction = max(final_predictions, key=lambda x: x['confidence'])
            
            return {
                'predicted': True,
                'location': {'latitude': lat, 'longitude': lon},
                'mcc': best_prediction['mcc'],
                'confidence': min(0.95, best_prediction['confidence']),
                'method': 'historical_area_analysis',
                'primary_methods': best_prediction['methods'],
                'all_predictions': final_predictions,
                'analysis_details': {
                    'transaction_analysis': transaction_analysis,
                    'merchant_analysis': merchant_analysis,
                    'temporal_analysis': temporal_analysis,
                    'behavioral_analysis': behavioral_analysis,
                    'density_analysis': density_analysis
                },
                'confidence_factors': confidence_factors,
                'area_characteristics': {
                    'data_richness': len([a for a in [transaction_analysis, merchant_analysis, 
                                                    temporal_analysis, behavioral_analysis] if a.get('analyzed')]),
                    'transaction_density': density_analysis.get('density_per_km2', 0),
                    'merchant_density': merchant_analysis.get('area_characteristics', {}).get('merchant_density', 0)
                }
            }
        
        # No strong predictions available
        return {
            'predicted': False,
            'location': {'latitude': lat, 'longitude': lon},
            'mcc': '5999',  # Default fallback
            'confidence': 0.1,
            'method': 'historical_analysis_insufficient_data',
            'analysis_details': {
                'transaction_analysis': transaction_analysis,
                'merchant_analysis': merchant_analysis,
                'temporal_analysis': temporal_analysis,
                'behavioral_analysis': behavioral_analysis,
                'density_analysis': density_analysis
            },
            'confidence_factors': confidence_factors
        }
    
    def _calculate_mcc_entropy(self, mcc_counts: Counter) -> float:
        """Calculate entropy of MCC distribution"""
        if not mcc_counts:
            return 0.0
        
        total = sum(mcc_counts.values())
        entropy = 0.0
        
        for count in mcc_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    async def _get_cached_area_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached area analysis result"""
        try:
            if not self.supabase:
                return None
            
            result = await self.supabase.table('area_pattern_cache').select('*').eq(
                'cache_key', cache_key
            ).order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                cache_entry = result.data[0]
                return {
                    'data': json.loads(cache_entry['analysis_data']),
                    'cached_at': datetime.fromisoformat(cache_entry['created_at'].replace('Z', '+00:00'))
                }
        
        except Exception as e:
            logger.error(f"Error retrieving cached area analysis: {str(e)}")
        
        return None
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        cached_at = cached_result['cached_at']
        return datetime.now() - cached_at < self.cache_duration
    
    def _enhance_cached_analysis(self, cached_result: Dict[str, Any], 
                                transaction_amount: Optional[float],
                                transaction_time: Optional[datetime]) -> Dict[str, Any]:
        """Enhance cached analysis with current transaction context"""
        
        base_result = cached_result['data']
        
        # Add real-time context if available
        if transaction_amount or transaction_time:
            base_result['enhanced_with_current_context'] = True
            base_result['context_timestamp'] = datetime.now().isoformat()
            
            # Could add real-time behavioral matching here
            if transaction_amount:
                base_result['current_amount_context'] = transaction_amount
            if transaction_time:
                base_result['current_time_context'] = transaction_time.isoformat()
        
        return base_result
    
    async def _cache_area_analysis(self, cache_key: str, analysis: Dict[str, Any]):
        """Cache area analysis result"""
        try:
            if not self.supabase:
                return
            
            await self.supabase.table('area_pattern_cache').upsert({
                'cache_key': cache_key,
                'analysis_data': json.dumps(analysis),
                'created_at': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error caching area analysis: {str(e)}")
    
    def _get_empty_analysis_result(self) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            'predicted': False,
            'location': {'latitude': 0, 'longitude': 0},
            'mcc': '5999',
            'confidence': 0.0,
            'method': 'historical_analysis_failed',
            'analysis_details': {},
            'confidence_factors': {}
        }
    
    async def store_transaction_data(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store transaction data for future historical analysis"""
        try:
            if not self.supabase or not transaction_data:
                return {'success': False, 'error': 'Invalid input'}
            
            # Enrich transaction data with spatial indexing
            if transaction_data.get('latitude') and transaction_data.get('longitude'):
                h3_hex = h3.geo_to_h3(
                    transaction_data['latitude'], 
                    transaction_data['longitude'], 
                    self.h3_resolution
                )
                transaction_data['h3_hex'] = h3_hex
            
            # Store in transaction history
            storage_data = {
                'transaction_id': transaction_data.get('transaction_id'),
                'merchant_name': transaction_data.get('merchant_name'),
                'mcc': transaction_data.get('mcc'),
                'amount': transaction_data.get('amount'),
                'latitude': transaction_data.get('latitude'),
                'longitude': transaction_data.get('longitude'),
                'h3_hex': transaction_data.get('h3_hex'),
                'transaction_time': transaction_data.get('transaction_time', datetime.now().isoformat()),
                'success': transaction_data.get('success', True),
                'card_type': transaction_data.get('card_type'),
                'has_tip': transaction_data.get('has_tip', False),
                'terminal_id': transaction_data.get('terminal_id'),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('transaction_history').insert(storage_data).execute()
            
            return {'success': True, 'transaction_id': transaction_data.get('transaction_id')}
            
        except Exception as e:
            logger.error(f"Error storing transaction data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_area_statistics(self, lat: float, lon: float, radius_meters: int = 500) -> Dict[str, Any]:
        """Get comprehensive statistics for an area"""
        try:
            if not self.supabase:
                return {'error': 'Database not available'}
            
            # Get comprehensive area statistics
            result = await self.supabase.rpc('get_area_comprehensive_stats', {
                'center_lat': lat,
                'center_lon': lon,
                'radius_meters': radius_meters,
                'days_back': 90
            }).execute()
            
            if result.data:
                stats = result.data[0]
                
                return {
                    'location': {'latitude': lat, 'longitude': lon, 'radius_meters': radius_meters},
                    'transaction_statistics': {
                        'total_transactions': stats.get('total_transactions', 0),
                        'unique_merchants': stats.get('unique_merchants', 0),
                        'unique_mccs': stats.get('unique_mccs', 0),
                        'avg_amount': stats.get('avg_amount', 0),
                        'total_volume': stats.get('total_volume', 0)
                    },
                    'temporal_statistics': {
                        'peak_hour': stats.get('peak_hour'),
                        'peak_day': stats.get('peak_day'),
                        'activity_spread': stats.get('activity_spread', 0)
                    },
                    'mcc_distribution': json.loads(stats.get('mcc_distribution', '{}')),
                    'confidence_metrics': {
                        'data_density': min(1.0, stats.get('total_transactions', 0) / 100),
                        'temporal_consistency': stats.get('temporal_consistency', 0),
                        'merchant_consistency': stats.get('merchant_consistency', 0)
                    }
                }
            else:
                return {
                    'location': {'latitude': lat, 'longitude': lon, 'radius_meters': radius_meters},
                    'message': 'No historical data available for this area'
                }
            
        except Exception as e:
            logger.error(f"Error getting area statistics: {str(e)}")
            return {'error': str(e)} 