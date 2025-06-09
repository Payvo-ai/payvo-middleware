"""
Supabase Database Client
Handles all database operations using Supabase
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase client wrapper for database operations
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if settings.use_supabase:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_ANON_KEY
                )
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("Supabase not configured - using fallback storage")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    # Transaction History Operations
    
    async def store_transaction_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Store transaction feedback for learning"""
        if not self.is_available:
            return False
        
        try:
            # Prepare data for Supabase
            data = {
                "session_id": feedback_data.get("session_id"),
                "user_id": feedback_data.get("user_id"),
                "predicted_mcc": feedback_data.get("predicted_mcc"),
                "actual_mcc": feedback_data.get("actual_mcc"),
                "prediction_confidence": feedback_data.get("prediction_confidence"),
                "prediction_method": feedback_data.get("prediction_method"),
                "selected_card_id": feedback_data.get("selected_card_id"),
                "network_used": feedback_data.get("network_used"),
                "transaction_success": feedback_data.get("transaction_success"),
                "rewards_earned": feedback_data.get("rewards_earned"),
                "merchant_name": feedback_data.get("merchant_name"),
                "transaction_amount": feedback_data.get("transaction_amount"),
                "location_lat": feedback_data.get("location_lat"),
                "location_lng": feedback_data.get("location_lng"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("transaction_feedback").insert(data).execute()
            
            if result.data:
                logger.info(f"Transaction feedback stored for session {feedback_data.get('session_id')}")
                return True
            else:
                logger.error("Failed to store transaction feedback")
                return False
                
        except Exception as e:
            logger.error(f"Error storing transaction feedback: {e}")
            return False
    
    async def get_user_transaction_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get user's transaction history for pattern analysis"""
        if not self.is_available:
            return []
        
        try:
            result = self.client.table("transaction_feedback")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user transaction history: {e}")
            return []
    
    # MCC Learning Operations
    
    async def store_mcc_prediction_result(self, prediction_data: Dict[str, Any]) -> bool:
        """Store MCC prediction results for learning"""
        if not self.is_available:
            return False
        
        try:
            data = {
                "session_id": prediction_data.get("session_id"),
                "terminal_id": prediction_data.get("terminal_id"),
                "location_hash": prediction_data.get("location_hash"),
                "wifi_fingerprint": prediction_data.get("wifi_fingerprint"),
                "ble_fingerprint": prediction_data.get("ble_fingerprint"),
                "predicted_mcc": prediction_data.get("predicted_mcc"),
                "confidence": prediction_data.get("confidence"),
                "method_used": prediction_data.get("method_used"),
                "context_features": prediction_data.get("context_features"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("mcc_predictions").insert(data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error storing MCC prediction: {e}")
            return False
    
    async def get_terminal_mcc_history(self, terminal_id: str) -> List[Dict]:
        """Get MCC history for a specific terminal"""
        if not self.is_available:
            return []
        
        try:
            result = self.client.table("transaction_feedback")\
                .select("actual_mcc, created_at")\
                .eq("terminal_id", terminal_id)\
                .not_.is_("actual_mcc", "null")\
                .order("created_at", desc=True)\
                .limit(50)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching terminal MCC history: {e}")
            return []
    
    async def get_location_mcc_history(self, location_hash: str) -> List[Dict]:
        """Get MCC history for a specific location"""
        if not self.is_available:
            return []
        
        try:
            result = self.client.table("transaction_feedback")\
                .select("actual_mcc, created_at, merchant_name")\
                .eq("location_hash", location_hash)\
                .not_.is_("actual_mcc", "null")\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching location MCC history: {e}")
            return []
    
    # Card Performance Operations
    
    async def store_card_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Store card performance metrics"""
        if not self.is_available:
            return False
        
        try:
            data = {
                "card_id": performance_data.get("card_id"),
                "user_id": performance_data.get("user_id"),
                "mcc": performance_data.get("mcc"),
                "network": performance_data.get("network"),
                "transaction_success": performance_data.get("transaction_success"),
                "rewards_earned": performance_data.get("rewards_earned"),
                "transaction_amount": performance_data.get("transaction_amount"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("card_performance").insert(data).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error storing card performance: {e}")
            return False
    
    async def get_card_performance_stats(self, card_id: str, mcc: str = None) -> Dict[str, Any]:
        """Get performance statistics for a card"""
        if not self.is_available:
            return {}
        
        try:
            query = self.client.table("card_performance")\
                .select("*")\
                .eq("card_id", card_id)
            
            if mcc:
                query = query.eq("mcc", mcc)
            
            result = query.execute()
            
            if not result.data:
                return {}
            
            # Calculate statistics
            transactions = result.data
            total_transactions = len(transactions)
            successful_transactions = sum(1 for t in transactions if t.get("transaction_success"))
            total_rewards = sum(t.get("rewards_earned", 0) for t in transactions)
            
            return {
                "total_transactions": total_transactions,
                "success_rate": successful_transactions / total_transactions if total_transactions > 0 else 0,
                "total_rewards": total_rewards,
                "average_rewards": total_rewards / total_transactions if total_transactions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching card performance stats: {e}")
            return {}
    
    # User Profile Operations
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user's card and routing preferences"""
        if not self.is_available:
            return {}
        
        try:
            result = self.client.table("user_preferences")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user's preferences"""
        if not self.is_available:
            return False
        
        try:
            data = {
                "user_id": user_id,
                "preferences": preferences,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Try to update first, then insert if not exists
            result = self.client.table("user_preferences")\
                .upsert(data)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    # Analytics Operations
    
    async def get_system_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide analytics"""
        if not self.is_available:
            return {}
        
        try:
            cutoff_date = (datetime.utcnow().timestamp() - (days * 24 * 60 * 60)) * 1000
            
            # Get prediction accuracy
            result = self.client.table("transaction_feedback")\
                .select("predicted_mcc, actual_mcc, prediction_confidence")\
                .gte("created_at", datetime.fromtimestamp(cutoff_date/1000).isoformat())\
                .not_.is_("actual_mcc", "null")\
                .execute()
            
            if not result.data:
                return {}
            
            transactions = result.data
            correct_predictions = sum(
                1 for t in transactions 
                if t.get("predicted_mcc") == t.get("actual_mcc")
            )
            
            total_predictions = len(transactions)
            avg_confidence = sum(t.get("prediction_confidence", 0) for t in transactions) / total_predictions
            
            return {
                "total_predictions": total_predictions,
                "accuracy_rate": correct_predictions / total_predictions if total_predictions > 0 else 0,
                "average_confidence": avg_confidence,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error fetching system analytics: {e}")
            return {}


# Global instance - lazy loaded
_supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get the global Supabase client instance (lazy loaded)"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

# Create a property-like object for backward compatibility
class SupabaseClientProxy:
    @property
    def is_available(self) -> bool:
        return get_supabase_client().is_available
    
    async def store_transaction_feedback(self, feedback_data):
        return await get_supabase_client().store_transaction_feedback(feedback_data)
    
    async def get_user_transaction_history(self, user_id: str, limit: int = 100):
        return await get_supabase_client().get_user_transaction_history(user_id, limit)
    
    async def store_mcc_prediction_result(self, prediction_data):
        return await get_supabase_client().store_mcc_prediction_result(prediction_data)
    
    async def get_terminal_mcc_history(self, terminal_id: str, limit: int = 50):
        return await get_supabase_client().get_terminal_mcc_history(terminal_id)
    
    async def get_location_mcc_history(self, location_hash: str, limit: int = 50):
        return await get_supabase_client().get_location_mcc_history(location_hash)
    
    async def store_card_performance(self, performance_data):
        return await get_supabase_client().store_card_performance(performance_data)
    
    async def get_card_performance_stats(self, card_id: str, days: int = 30):
        return await get_supabase_client().get_card_performance_stats(card_id)
    
    async def get_user_preferences(self, user_id: str):
        return await get_supabase_client().get_user_preferences(user_id)
    
    async def update_user_preferences(self, user_id: str, preferences):
        return await get_supabase_client().update_user_preferences(user_id, preferences)
    
    async def get_system_analytics(self, days: int = 7):
        return await get_supabase_client().get_system_analytics(days)

supabase_client = SupabaseClientProxy() 