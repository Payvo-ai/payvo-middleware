"""
Database connection manager
Handles Supabase connections for data storage and retrieval
"""

import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.database.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """Manages database connections using Supabase"""
    
    def __init__(self):
        self._supabase_available = None
        # Don't check connections immediately - do it lazily
    
    def _check_connections(self):
        """Check availability of Supabase connection"""
        if self._supabase_available is None:
            # Check Supabase availability
            self._supabase_available = supabase_client.is_available
            if self._supabase_available:
                logger.info("Supabase connection is available")
            else:
                logger.warning("Supabase connection is not available")
            
            if not self._supabase_available:
                logger.error("No database connection available!")
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase connection is available"""
        self._check_connections()
        return self._supabase_available
    
    @property
    def use_supabase(self) -> bool:
        """Check if we should use Supabase (always true if available)"""
        self._check_connections()
        return self._supabase_available
    
    async def store_transaction_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Store transaction feedback using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for storing transaction feedback")
            return False
        
        return await supabase_client.store_transaction_feedback(feedback_data)
    
    async def get_user_transaction_history(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user transaction history using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving transaction history")
            return []
        
        return await supabase_client.get_user_transaction_history(user_id, limit)
    
    async def store_mcc_prediction_result(self, prediction_data: Dict[str, Any]) -> bool:
        """Store MCC prediction result using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for storing MCC prediction")
            return False
        
        return await supabase_client.store_mcc_prediction_result(prediction_data)
    
    async def get_terminal_mcc_history(self, terminal_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get terminal MCC history using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving terminal history")
            return []
        
        return await supabase_client.get_terminal_mcc_history(terminal_id, limit)
    
    async def get_location_mcc_history(self, location_hash: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get location MCC history using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving location history")
            return []
        
        return await supabase_client.get_location_mcc_history(location_hash, limit)
    
    async def store_card_performance(self, performance_data: Dict[str, Any]) -> bool:
        """Store card performance data using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for storing card performance")
            return False
        
        return await supabase_client.store_card_performance(performance_data)
    
    async def get_card_performance_stats(self, card_id: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get card performance statistics using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving card performance")
            return None
        
        return await supabase_client.get_card_performance_stats(card_id, days)
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving user preferences")
            return {}
        
        return await supabase_client.get_user_preferences(user_id)
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for updating user preferences")
            return False
        
        return await supabase_client.update_user_preferences(user_id, preferences)
    
    async def get_system_analytics(self, days: int = 7) -> Optional[Dict[str, Any]]:
        """Get system analytics using Supabase"""
        if not self.is_available:
            logger.error("No database connection available for retrieving system analytics")
            return None
        
        return await supabase_client.get_system_analytics(days)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Supabase connection"""
        return {
            "supabase_available": self._supabase_available,
            "overall_status": "healthy" if self.is_available else "unhealthy"
        }


# Global connection manager instance
connection_manager = DatabaseConnectionManager() 