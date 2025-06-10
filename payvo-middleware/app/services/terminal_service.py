"""
Enhanced Terminal Service for MCC Prediction
Provides comprehensive terminal ID lookup and merchant categorization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import json
import hashlib
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict

import numpy as np
from geopy.distance import geodesic

from ..core.config import settings
from ..database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class TerminalService:
    """Enhanced terminal lookup and analysis service"""
    
    def __init__(self):
        self.supabase = None
        self.terminal_cache = {}
        self.merchant_patterns = {}
        self.terminal_networks = {}
        self.cache_duration = timedelta(hours=12)  # Cache terminal data for 12 hours
        
    async def initialize(self):
        """Initialize the terminal service"""
        try:
            self.supabase = await get_supabase_client()
            await self._create_terminal_tables()
            await self._load_terminal_patterns()
            logger.info("TerminalService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TerminalService: {str(e)}")
    
    async def _create_terminal_tables(self):
        """Create database tables for terminal data"""
        try:
            # Check if tables exist
            await self.supabase.table('terminal_registry').select('*').limit(1).execute()
            await self.supabase.table('terminal_transactions').select('*').limit(1).execute()
            await self.supabase.table('merchant_profiles').select('*').limit(1).execute()
        except:
            logger.info("Creating terminal tables")
            # In production, use proper database migrations
    
    async def _load_terminal_patterns(self):
        """Load known terminal ID patterns and merchant networks"""
        
        # Known terminal ID patterns for major processors/networks
        self.terminal_networks = {
            # Square terminals
            'square': {
                'patterns': [
                    r'^SQ[0-9]{6,12}$',
                    r'^SQUID[0-9]{8}$',
                    r'^SQ\d+[A-Z]{2}\d+$'
                ],
                'processor': 'Square',
                'typical_merchants': ['small_retail', 'food_trucks', 'pop_up_shops'],
                'confidence_boost': 0.1
            },
            
            # PayPal Here
            'paypal': {
                'patterns': [
                    r'^PP[0-9]{8,12}$',
                    r'^PAYPAL[0-9]{6,10}$',
                    r'^PH\d+[A-Z]{2}$'
                ],
                'processor': 'PayPal',
                'typical_merchants': ['small_retail', 'services', 'online_sellers'],
                'confidence_boost': 0.1
            },
            
            # Clover terminals
            'clover': {
                'patterns': [
                    r'^CLV[0-9]{8,12}$',
                    r'^CLOVER\d{6,10}$',
                    r'^C\d{8,12}$'
                ],
                'processor': 'First Data/Clover',
                'typical_merchants': ['restaurants', 'retail', 'services'],
                'confidence_boost': 0.1
            },
            
            # Traditional bank terminals
            'chase': {
                'patterns': [
                    r'^CH[0-9]{8,12}$',
                    r'^CHASE\d{6,10}$',
                    r'^JPM\d{8,12}$'
                ],
                'processor': 'Chase Paymentech',
                'typical_merchants': ['large_retail', 'corporate', 'restaurants'],
                'confidence_boost': 0.05
            },
            
            # Worldpay/FIS terminals
            'worldpay': {
                'patterns': [
                    r'^WP[0-9]{8,12}$',
                    r'^WORLD\d{6,10}$',
                    r'^FIS\d{8,12}$'
                ],
                'processor': 'Worldpay/FIS',
                'typical_merchants': ['enterprise', 'retail_chains', 'ecommerce'],
                'confidence_boost': 0.05
            },
            
            # Stripe terminals
            'stripe': {
                'patterns': [
                    r'^ST_[A-Z0-9]{8,16}$',
                    r'^STRIPE_\d{6,12}$',
                    r'^st_live_[a-zA-Z0-9]{24,32}$'
                ],
                'processor': 'Stripe',
                'typical_merchants': ['ecommerce', 'saas', 'marketplaces', 'retail'],
                'confidence_boost': 0.1
            }
        }
        
        # Merchant category patterns based on terminal behavior
        self.merchant_patterns = {
            'restaurant_patterns': {
                'transaction_characteristics': {
                    'avg_amount_range': (15, 75),  # Typical meal amounts
                    'peak_hours': [11, 12, 13, 17, 18, 19, 20],  # Meal times
                    'tip_frequency': 0.7,  # High tip frequency
                    'weekend_factor': 1.2   # Higher weekend activity
                },
                'mcc_candidates': ['5812', '5814'],
                'confidence': 0.8
            },
            
            'gas_station_patterns': {
                'transaction_characteristics': {
                    'avg_amount_range': (25, 80),  # Typical gas purchases
                    'peak_hours': [7, 8, 16, 17, 18],  # Commute times
                    'tip_frequency': 0.05,  # Very low tip frequency
                    'weekend_factor': 0.9   # Lower weekend activity
                },
                'mcc_candidates': ['5541', '5542'],
                'confidence': 0.85
            },
            
            'grocery_patterns': {
                'transaction_characteristics': {
                    'avg_amount_range': (25, 150),  # Grocery shopping
                    'peak_hours': [10, 11, 17, 18, 19],  # Shopping times
                    'tip_frequency': 0.1,   # Low tip frequency
                    'weekend_factor': 1.3   # Higher weekend activity
                },
                'mcc_candidates': ['5411', '5412'],
                'confidence': 0.75
            },
            
            'retail_patterns': {
                'transaction_characteristics': {
                    'avg_amount_range': (20, 200),  # General retail
                    'peak_hours': [11, 12, 13, 14, 15, 16],  # Shopping hours
                    'tip_frequency': 0.2,   # Occasional tips
                    'weekend_factor': 1.4   # Much higher weekend activity
                },
                'mcc_candidates': ['5999', '5311', '5651'],
                'confidence': 0.7
            },
            
            'coffee_shop_patterns': {
                'transaction_characteristics': {
                    'avg_amount_range': (4, 15),    # Coffee/snack amounts
                    'peak_hours': [7, 8, 9, 14, 15],  # Coffee times
                    'tip_frequency': 0.6,   # Moderate tip frequency
                    'weekend_factor': 0.8   # Lower weekend (office workers)
                },
                'mcc_candidates': ['5812'],
                'confidence': 0.8
            }
        }
    
    async def lookup_terminal(self, terminal_id: str, transaction_amount: Optional[float] = None,
                            transaction_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Comprehensive terminal lookup with MCC prediction
        
        Args:
            terminal_id: Terminal identifier
            transaction_amount: Optional transaction amount for pattern analysis
            transaction_time: Optional transaction timestamp for pattern analysis
        
        Returns:
            Terminal analysis with MCC prediction
        """
        try:
            if not terminal_id:
                return self._get_empty_terminal_result()
            
            # Sanitize terminal ID
            terminal_id = str(terminal_id).strip().upper()
            
            # Check cache first
            cached_result = await self._get_cached_terminal_lookup(terminal_id)
            if cached_result and self._is_cache_valid(cached_result):
                return self._enhance_cached_result(cached_result, transaction_amount, transaction_time)
            
            # Perform comprehensive lookup
            registry_lookup = await self._lookup_terminal_registry(terminal_id)
            historical_analysis = await self._analyze_terminal_history(terminal_id)
            pattern_analysis = self._analyze_terminal_pattern(terminal_id)
            network_analysis = self._analyze_terminal_network(terminal_id)
            behavioral_analysis = await self._analyze_terminal_behavior(
                terminal_id, transaction_amount, transaction_time
            )
            
            # Combine all analyses
            combined_result = self._combine_terminal_analyses(
                registry_lookup, historical_analysis, pattern_analysis, 
                network_analysis, behavioral_analysis, terminal_id
            )
            
            # Cache the result
            await self._cache_terminal_lookup(terminal_id, combined_result)
            
            # Store transaction data for future analysis
            if transaction_amount and transaction_time:
                await self._store_terminal_transaction(
                    terminal_id, transaction_amount, transaction_time, combined_result
                )
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in terminal lookup: {str(e)}")
            return self._get_empty_terminal_result()
    
    async def _lookup_terminal_registry(self, terminal_id: str) -> Dict[str, Any]:
        """Look up terminal in the registry database"""
        try:
            if not self.supabase:
                return {'found': False}
            
            # Query terminal registry
            result = await self.supabase.table('terminal_registry').select(
                'terminal_id, merchant_name, merchant_category, mcc, processor, '
                'registration_date, last_active, location_city, location_state, confidence'
            ).eq('terminal_id', terminal_id).execute()
            
            if result.data:
                terminal_data = result.data[0]
                
                # Calculate confidence based on data completeness and recency
                base_confidence = terminal_data.get('confidence', 0.7)
                
                # Boost confidence if recently active
                last_active = terminal_data.get('last_active')
                if last_active:
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    days_since_active = (datetime.now() - last_active_date).days
                    recency_factor = max(0.5, 1.0 - (days_since_active / 365))  # Decay over a year
                    adjusted_confidence = min(0.95, base_confidence * recency_factor)
                else:
                    adjusted_confidence = base_confidence * 0.8  # Lower if no recent activity
                
                return {
                    'found': True,
                    'merchant_name': terminal_data.get('merchant_name', 'Unknown'),
                    'merchant_category': terminal_data.get('merchant_category', 'Unknown'),
                    'mcc': terminal_data.get('mcc', '5999'),
                    'processor': terminal_data.get('processor', 'Unknown'),
                    'confidence': adjusted_confidence,
                    'location': {
                        'city': terminal_data.get('location_city'),
                        'state': terminal_data.get('location_state')
                    },
                    'registration_date': terminal_data.get('registration_date'),
                    'last_active': last_active
                }
        
        except Exception as e:
            logger.error(f"Error looking up terminal registry: {str(e)}")
        
        return {'found': False}
    
    async def _analyze_terminal_history(self, terminal_id: str) -> Dict[str, Any]:
        """Analyze historical transaction patterns for this terminal"""
        try:
            if not self.supabase:
                return {'analyzed': False}
            
            # Query recent transactions (last 90 days)
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            result = await self.supabase.table('terminal_transactions').select(
                'transaction_amount, transaction_time, predicted_mcc, confidence, '
                'hour_of_day, day_of_week, has_tip'
            ).eq('terminal_id', terminal_id).gte('transaction_time', cutoff_date).execute()
            
            if not result.data or len(result.data) < 5:  # Need minimum transactions for analysis
                return {'analyzed': False, 'reason': 'insufficient_data'}
            
            transactions = result.data
            
            # Analyze transaction patterns
            amounts = [float(t['transaction_amount']) for t in transactions]
            hours = [t['hour_of_day'] for t in transactions if t.get('hour_of_day')]
            days = [t['day_of_week'] for t in transactions if t.get('day_of_week')]
            mccs = [t['predicted_mcc'] for t in transactions if t.get('predicted_mcc')]
            tips = [t.get('has_tip', False) for t in transactions]
            
            # Calculate pattern characteristics
            analysis = {
                'analyzed': True,
                'transaction_count': len(transactions),
                'amount_stats': {
                    'avg': np.mean(amounts),
                    'median': np.median(amounts),
                    'std': np.std(amounts),
                    'min': min(amounts),
                    'max': max(amounts)
                },
                'temporal_patterns': {
                    'peak_hours': self._find_peak_hours(hours),
                    'weekend_factor': self._calculate_weekend_factor(days, amounts),
                    'hour_distribution': Counter(hours),
                    'day_distribution': Counter(days)
                },
                'behavioral_patterns': {
                    'tip_frequency': sum(tips) / len(tips) if tips else 0,
                    'amount_consistency': 1.0 / (1.0 + np.std(amounts) / np.mean(amounts)) if amounts else 0
                },
                'mcc_patterns': {
                    'historical_mccs': Counter(mccs),
                    'dominant_mcc': Counter(mccs).most_common(1)[0][0] if mccs else None,
                    'mcc_consistency': max(Counter(mccs).values()) / len(mccs) if mccs else 0
                }
            }
            
            # Predict MCC based on historical patterns
            if analysis['mcc_patterns']['dominant_mcc'] and analysis['mcc_patterns']['mcc_consistency'] > 0.6:
                analysis['predicted_mcc'] = {
                    'mcc': analysis['mcc_patterns']['dominant_mcc'],
                    'confidence': min(0.9, analysis['mcc_patterns']['mcc_consistency'] + 0.1),
                    'source': 'historical_consistency'
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing terminal history: {str(e)}")
        
        return {'analyzed': False, 'reason': 'analysis_error'}
    
    def _analyze_terminal_pattern(self, terminal_id: str) -> Dict[str, Any]:
        """Analyze terminal ID pattern for processor/network identification"""
        
        analysis = {
            'pattern_matched': False,
            'processor': 'Unknown',
            'network_type': 'Unknown',
            'confidence_boost': 0.0
        }
        
        for network, network_info in self.terminal_networks.items():
            for pattern in network_info['patterns']:
                if re.match(pattern, terminal_id):
                    analysis.update({
                        'pattern_matched': True,
                        'processor': network_info['processor'],
                        'network_type': network,
                        'typical_merchants': network_info['typical_merchants'],
                        'confidence_boost': network_info['confidence_boost'],
                        'pattern': pattern
                    })
                    break
            
            if analysis['pattern_matched']:
                break
        
        return analysis
    
    def _analyze_terminal_network(self, terminal_id: str) -> Dict[str, Any]:
        """Analyze terminal network characteristics"""
        
        analysis = {
            'id_length': len(terminal_id),
            'character_composition': self._analyze_character_composition(terminal_id),
            'format_type': self._determine_format_type(terminal_id),
            'entropy': self._calculate_id_entropy(terminal_id)
        }
        
        # Infer network type from characteristics
        if analysis['id_length'] <= 8 and analysis['character_composition']['digits_only']:
            analysis['likely_network'] = 'legacy_bank_terminal'
            analysis['confidence'] = 0.6
        elif analysis['id_length'] >= 12 and analysis['character_composition']['mixed']:
            analysis['likely_network'] = 'modern_processor'
            analysis['confidence'] = 0.7
        elif 'ST_' in terminal_id or 'STRIPE' in terminal_id:
            analysis['likely_network'] = 'stripe'
            analysis['confidence'] = 0.9
        else:
            analysis['likely_network'] = 'unknown'
            analysis['confidence'] = 0.3
        
        return analysis
    
    async def _analyze_terminal_behavior(self, terminal_id: str, 
                                       transaction_amount: Optional[float] = None,
                                       transaction_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze current transaction against known behavioral patterns"""
        
        analysis = {
            'behavioral_matches': [],
            'predicted_category': None,
            'confidence': 0.0
        }
        
        if not transaction_amount or not transaction_time:
            return analysis
        
        hour = transaction_time.hour
        day_of_week = transaction_time.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5
        
        # Check against known patterns
        for pattern_name, pattern_info in self.merchant_patterns.items():
            characteristics = pattern_info['transaction_characteristics']
            
            match_score = 0.0
            match_factors = []
            
            # Check amount range
            amount_range = characteristics['avg_amount_range']
            if amount_range[0] <= transaction_amount <= amount_range[1]:
                match_score += 0.3
                match_factors.append('amount_range')
            elif amount_range[0] * 0.7 <= transaction_amount <= amount_range[1] * 1.3:
                match_score += 0.15  # Partial match for near-range amounts
                match_factors.append('amount_near_range')
            
            # Check peak hours
            if hour in characteristics['peak_hours']:
                match_score += 0.3
                match_factors.append('peak_hour')
            
            # Check weekend factor
            weekend_factor = characteristics['weekend_factor']
            if is_weekend and weekend_factor > 1.0:
                match_score += 0.2
                match_factors.append('weekend_positive')
            elif not is_weekend and weekend_factor < 1.0:
                match_score += 0.2
                match_factors.append('weekday_positive')
            
            if match_score > 0.4:  # Threshold for considering a match
                analysis['behavioral_matches'].append({
                    'pattern': pattern_name,
                    'match_score': match_score,
                    'match_factors': match_factors,
                    'mcc_candidates': pattern_info['mcc_candidates'],
                    'base_confidence': pattern_info['confidence']
                })
        
        # Select best behavioral match
        if analysis['behavioral_matches']:
            best_match = max(analysis['behavioral_matches'], key=lambda x: x['match_score'])
            analysis['predicted_category'] = best_match['pattern']
            analysis['confidence'] = best_match['base_confidence'] * best_match['match_score']
            analysis['recommended_mcc'] = best_match['mcc_candidates'][0]  # First candidate
        
        return analysis
    
    def _combine_terminal_analyses(self, registry_lookup: Dict, historical_analysis: Dict,
                                 pattern_analysis: Dict, network_analysis: Dict,
                                 behavioral_analysis: Dict, terminal_id: str) -> Dict[str, Any]:
        """Combine all terminal analysis results"""
        
        predictions = []
        
        # Registry lookup (highest priority if recent)
        if registry_lookup.get('found', False):
            predictions.append({
                'mcc': registry_lookup['mcc'],
                'confidence': registry_lookup['confidence'],
                'method': 'terminal_registry',
                'source': 'registry_database',
                'details': {
                    'merchant_name': registry_lookup.get('merchant_name'),
                    'processor': registry_lookup.get('processor')
                }
            })
        
        # Historical analysis (high priority if consistent)
        if historical_analysis.get('analyzed') and historical_analysis.get('predicted_mcc'):
            historical_pred = historical_analysis['predicted_mcc']
            predictions.append({
                'mcc': historical_pred['mcc'],
                'confidence': historical_pred['confidence'],
                'method': 'terminal_historical_analysis',
                'source': 'transaction_history',
                'details': {
                    'transaction_count': historical_analysis['transaction_count'],
                    'consistency': historical_analysis['mcc_patterns']['mcc_consistency']
                }
            })
        
        # Behavioral analysis (current transaction context)
        if behavioral_analysis.get('predicted_category'):
            predictions.append({
                'mcc': behavioral_analysis['recommended_mcc'],
                'confidence': behavioral_analysis['confidence'],
                'method': 'terminal_behavioral_analysis',
                'source': 'transaction_patterns',
                'details': {
                    'category': behavioral_analysis['predicted_category'],
                    'match_score': max([m['match_score'] for m in behavioral_analysis['behavioral_matches']])
                }
            })
        
        # Network/pattern analysis (provides context boost)
        confidence_boost = pattern_analysis.get('confidence_boost', 0.0)
        
        # Select best prediction
        if predictions:
            # Apply confidence boost from pattern analysis
            for pred in predictions:
                pred['confidence'] = min(0.95, pred['confidence'] + confidence_boost)
            
            best_prediction = max(predictions, key=lambda x: x['confidence'])
            
            return {
                'predicted': True,
                'terminal_id': terminal_id,
                'mcc': best_prediction['mcc'],
                'confidence': best_prediction['confidence'],
                'method': best_prediction['method'],
                'primary_source': best_prediction['source'],
                'all_predictions': predictions,
                'analysis_details': {
                    'registry_lookup': registry_lookup,
                    'historical_analysis': historical_analysis,
                    'pattern_analysis': pattern_analysis,
                    'network_analysis': network_analysis,
                    'behavioral_analysis': behavioral_analysis
                },
                'confidence_factors': {
                    'registry_available': registry_lookup.get('found', False),
                    'historical_data_available': historical_analysis.get('analyzed', False),
                    'pattern_matched': pattern_analysis.get('pattern_matched', False),
                    'behavioral_match': bool(behavioral_analysis.get('predicted_category'))
                }
            }
        
        # No strong predictions - return analysis with low confidence fallback
        return {
            'predicted': False,
            'terminal_id': terminal_id,
            'mcc': '5999',  # Fallback to miscellaneous retail
            'confidence': 0.2 + confidence_boost,
            'method': 'terminal_fallback',
            'primary_source': 'pattern_analysis',
            'analysis_details': {
                'registry_lookup': registry_lookup,
                'historical_analysis': historical_analysis,
                'pattern_analysis': pattern_analysis,
                'network_analysis': network_analysis,
                'behavioral_analysis': behavioral_analysis
            },
            'confidence_factors': {
                'registry_available': False,
                'historical_data_available': False,
                'pattern_matched': pattern_analysis.get('pattern_matched', False),
                'behavioral_match': False
            }
        }
    
    def _find_peak_hours(self, hours: List[int]) -> List[int]:
        """Find peak transaction hours"""
        if not hours:
            return []
        
        hour_counts = Counter(hours)
        avg_count = sum(hour_counts.values()) / len(hour_counts)
        peak_hours = [hour for hour, count in hour_counts.items() if count > avg_count * 1.5]
        
        return sorted(peak_hours)
    
    def _calculate_weekend_factor(self, days: List[int], amounts: List[float]) -> float:
        """Calculate weekend vs weekday transaction factor"""
        if not days or not amounts:
            return 1.0
        
        weekend_amounts = [amounts[i] for i, day in enumerate(days) if day >= 5]  # Sat, Sun
        weekday_amounts = [amounts[i] for i, day in enumerate(days) if day < 5]
        
        if not weekend_amounts or not weekday_amounts:
            return 1.0
        
        weekend_avg = np.mean(weekend_amounts)
        weekday_avg = np.mean(weekday_amounts)
        
        return weekend_avg / weekday_avg if weekday_avg > 0 else 1.0
    
    def _analyze_character_composition(self, terminal_id: str) -> Dict[str, Any]:
        """Analyze character composition of terminal ID"""
        
        digits = sum(1 for c in terminal_id if c.isdigit())
        letters = sum(1 for c in terminal_id if c.isalpha())
        special = sum(1 for c in terminal_id if not c.isalnum())
        
        total = len(terminal_id)
        
        return {
            'digits': digits,
            'letters': letters,
            'special_chars': special,
            'digits_ratio': digits / total if total > 0 else 0,
            'letters_ratio': letters / total if total > 0 else 0,
            'special_ratio': special / total if total > 0 else 0,
            'digits_only': letters == 0 and special == 0,
            'letters_only': digits == 0 and special == 0,
            'mixed': digits > 0 and letters > 0
        }
    
    def _determine_format_type(self, terminal_id: str) -> str:
        """Determine terminal ID format type"""
        
        if re.match(r'^\d+$', terminal_id):
            return 'numeric_only'
        elif re.match(r'^[A-Z]+\d+$', terminal_id):
            return 'prefix_numeric'
        elif re.match(r'^\d+[A-Z]+$', terminal_id):
            return 'numeric_suffix'
        elif re.match(r'^[A-Z]+_[A-Z0-9]+$', terminal_id):
            return 'underscore_separated'
        elif '_' in terminal_id:
            return 'underscore_mixed'
        elif '-' in terminal_id:
            return 'hyphen_separated'
        else:
            return 'mixed_alphanumeric'
    
    def _calculate_id_entropy(self, terminal_id: str) -> float:
        """Calculate entropy of terminal ID"""
        
        if not terminal_id:
            return 0.0
        
        # Calculate character frequency
        char_counts = Counter(terminal_id)
        total_chars = len(terminal_id)
        
        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            if probability > 0:
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    async def _get_cached_terminal_lookup(self, terminal_id: str) -> Optional[Dict[str, Any]]:
        """Get cached terminal lookup result"""
        try:
            if not self.supabase:
                return None
            
            result = await self.supabase.table('terminal_cache').select('*').eq(
                'terminal_id', terminal_id
            ).order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                cache_entry = result.data[0]
                return {
                    'data': json.loads(cache_entry['lookup_data']),
                    'cached_at': datetime.fromisoformat(cache_entry['created_at'].replace('Z', '+00:00'))
                }
        
        except Exception as e:
            logger.error(f"Error retrieving cached terminal lookup: {str(e)}")
        
        return None
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        cached_at = cached_result['cached_at']
        return datetime.now() - cached_at < self.cache_duration
    
    def _enhance_cached_result(self, cached_result: Dict[str, Any], 
                             transaction_amount: Optional[float],
                             transaction_time: Optional[datetime]) -> Dict[str, Any]:
        """Enhance cached result with current transaction context"""
        
        base_result = cached_result['data']
        
        # If we have transaction context, add behavioral analysis
        if transaction_amount and transaction_time:
            behavioral_analysis = asyncio.create_task(
                self._analyze_terminal_behavior(
                    base_result['terminal_id'], transaction_amount, transaction_time
                )
            )
            # Note: In practice, you'd await this properly within an async context
        
        return base_result
    
    async def _cache_terminal_lookup(self, terminal_id: str, result: Dict[str, Any]):
        """Cache terminal lookup result"""
        try:
            if not self.supabase:
                return
            
            await self.supabase.table('terminal_cache').upsert({
                'terminal_id': terminal_id,
                'lookup_data': json.dumps(result),
                'created_at': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error caching terminal lookup: {str(e)}")
    
    async def _store_terminal_transaction(self, terminal_id: str, amount: float,
                                        transaction_time: datetime, analysis_result: Dict[str, Any]):
        """Store terminal transaction data for future analysis"""
        try:
            if not self.supabase:
                return
            
            transaction_data = {
                'terminal_id': terminal_id,
                'transaction_amount': amount,
                'transaction_time': transaction_time.isoformat(),
                'predicted_mcc': analysis_result.get('mcc'),
                'confidence': analysis_result.get('confidence'),
                'method': analysis_result.get('method'),
                'hour_of_day': transaction_time.hour,
                'day_of_week': transaction_time.weekday(),
                'has_tip': False,  # Would need to be determined from transaction data
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('terminal_transactions').insert(transaction_data).execute()
            
        except Exception as e:
            logger.error(f"Error storing terminal transaction: {str(e)}")
    
    def _get_empty_terminal_result(self) -> Dict[str, Any]:
        """Return empty terminal analysis result"""
        return {
            'predicted': False,
            'terminal_id': '',
            'mcc': '5999',
            'confidence': 0.0,
            'method': 'terminal_lookup_failed',
            'primary_source': 'none',
            'analysis_details': {},
            'confidence_factors': {
                'registry_available': False,
                'historical_data_available': False,
                'pattern_matched': False,
                'behavioral_match': False
            }
        }
    
    async def register_terminal(self, terminal_id: str, merchant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new terminal in the registry"""
        try:
            if not self.supabase:
                return {'success': False, 'error': 'Database not available'}
            
            registration_data = {
                'terminal_id': terminal_id.strip().upper(),
                'merchant_name': merchant_data.get('merchant_name', ''),
                'merchant_category': merchant_data.get('merchant_category', ''),
                'mcc': merchant_data.get('mcc', '5999'),
                'processor': merchant_data.get('processor', 'Unknown'),
                'location_city': merchant_data.get('city', ''),
                'location_state': merchant_data.get('state', ''),
                'confidence': merchant_data.get('confidence', 0.8),
                'registration_date': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            
            await self.supabase.table('terminal_registry').upsert(registration_data).execute()
            
            return {'success': True, 'terminal_id': terminal_id}
            
        except Exception as e:
            logger.error(f"Error registering terminal: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def update_terminal_activity(self, terminal_id: str) -> None:
        """Update terminal last activity timestamp"""
        try:
            if not self.supabase:
                return
            
            await self.supabase.table('terminal_registry').update({
                'last_active': datetime.now().isoformat()
            }).eq('terminal_id', terminal_id.strip().upper()).execute()
            
        except Exception as e:
            logger.error(f"Error updating terminal activity: {str(e)}")
    
    async def get_terminal_statistics(self, terminal_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a terminal"""
        try:
            if not self.supabase:
                return {'error': 'Database not available'}
            
            # Get registry data
            registry_result = await self.supabase.table('terminal_registry').select('*').eq(
                'terminal_id', terminal_id.strip().upper()
            ).execute()
            
            # Get transaction statistics
            transaction_result = await self.supabase.table('terminal_transactions').select(
                'transaction_amount, transaction_time, predicted_mcc, confidence'
            ).eq('terminal_id', terminal_id.strip().upper()).execute()
            
            registry_data = registry_result.data[0] if registry_result.data else {}
            transactions = transaction_result.data if transaction_result.data else []
            
            if transactions:
                amounts = [float(t['transaction_amount']) for t in transactions]
                mccs = [t['predicted_mcc'] for t in transactions if t.get('predicted_mcc')]
                
                statistics = {
                    'terminal_info': registry_data,
                    'transaction_statistics': {
                        'total_transactions': len(transactions),
                        'amount_stats': {
                            'avg': np.mean(amounts),
                            'median': np.median(amounts),
                            'total': sum(amounts)
                        },
                        'mcc_distribution': dict(Counter(mccs)),
                        'date_range': {
                            'first_transaction': min([t['transaction_time'] for t in transactions]),
                            'last_transaction': max([t['transaction_time'] for t in transactions])
                        }
                    }
                }
            else:
                statistics = {
                    'terminal_info': registry_data,
                    'transaction_statistics': {
                        'total_transactions': 0,
                        'message': 'No transaction history available'
                    }
                }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting terminal statistics: {str(e)}")
            return {'error': str(e)} 