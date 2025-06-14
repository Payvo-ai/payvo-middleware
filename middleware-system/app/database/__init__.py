"""
Database layer for Payvo Middleware
Supports Supabase for data storage and retrieval
"""

from .connection_manager import connection_manager
from .supabase_client import supabase_client

def get_db():
    """
    Database dependency for FastAPI routes
    Returns the connection manager for database operations
    """
    return connection_manager

__all__ = ['connection_manager', 'supabase_client', 'get_db'] 