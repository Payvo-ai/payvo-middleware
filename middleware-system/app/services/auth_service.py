"""
Authentication Service for Payvo Middleware
Handles user authentication, session validation, and user context management
"""

import logging
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import jwt
import asyncio
from dataclasses import dataclass

from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AuthUser:
    """Authenticated user data"""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_verified: bool = False
    role: Optional[str] = None
    department: Optional[str] = None
    session_id: Optional[str] = None
    

@dataclass
class AuthSession:
    """Session validation result"""
    is_valid: bool
    user: Optional[AuthUser] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class AuthService:
    """
    Authentication service for validating users and managing sessions
    Integrates with Supabase Auth and provides middleware-specific functionality
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client for auth operations"""
        try:
            if settings.use_supabase:
                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for server-side operations
                )
                logger.info("🔐 Auth service initialized with Supabase")
            else:
                logger.warning("⚠️ Auth service initialized without Supabase - running in mock mode")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth service: {e}")
            self.client = None
    
    @property
    def is_available(self) -> bool:
        """Check if auth service is available"""
        return self.client is not None
    
    async def validate_session_token(self, token: str) -> AuthSession:
        """
        Validate a session token and return user information
        Supports both JWT tokens and custom session tokens
        """
        if not self.is_available:
            return AuthSession(
                is_valid=False,
                error="Authentication service not available"
            )
        
        try:
            # Try to validate as Supabase JWT first
            jwt_result = await self._validate_jwt_token(token)
            if jwt_result.is_valid:
                return jwt_result
            
            # Try to validate as custom session token
            session_result = await self._validate_custom_session(token)
            if session_result.is_valid:
                return session_result
            
            return AuthSession(
                is_valid=False,
                error="Invalid or expired token"
            )
            
        except Exception as e:
            logger.error(f"❌ Session validation failed: {e}")
            return AuthSession(
                is_valid=False,
                error=f"Validation error: {str(e)}"
            )
    
    async def _validate_jwt_token(self, token: str) -> AuthSession:
        """Validate Supabase JWT token"""
        try:
            # Get user from Supabase using the token
            self.client.auth.set_session(token, token)  # Set access token
            user_response = self.client.auth.get_user(token)
            
            if user_response.user:
                user_data = await self._get_user_profile(user_response.user.id)
                
                auth_user = AuthUser(
                    id=user_response.user.id,
                    email=user_response.user.email,
                    username=user_data.get('username'),
                    full_name=user_data.get('full_name'),
                    is_verified=user_data.get('is_verified', False),
                    role=user_data.get('role'),
                    department=user_data.get('department')
                )
                
                return AuthSession(
                    is_valid=True,
                    user=auth_user,
                    expires_at=datetime.fromtimestamp(user_response.user.last_sign_in_at, tz=timezone.utc) if user_response.user.last_sign_in_at else None
                )
            
            return AuthSession(is_valid=False, error="Invalid JWT token")
            
        except Exception as e:
            logger.debug(f"JWT validation failed: {e}")
            return AuthSession(is_valid=False, error="JWT validation failed")
    
    async def _validate_custom_session(self, session_token: str) -> AuthSession:
        """Validate custom session token from user_sessions table"""
        try:
            # Query user_sessions table using the session token
            result = self.client.table("user_sessions")\
                .select("*, user_profiles!inner(*)")\
                .eq("session_token", session_token)\
                .eq("is_active", True)\
                .gte("expires_at", datetime.utcnow().isoformat())\
                .execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                profile_data = session_data.get('user_profiles', {})
                
                auth_user = AuthUser(
                    id=session_data['user_id'],
                    email=profile_data.get('email'),  # Note: email might not be in user_profiles
                    username=profile_data.get('username'),
                    full_name=profile_data.get('full_name'),
                    is_verified=profile_data.get('is_verified', False),
                    role=profile_data.get('role'),
                    department=profile_data.get('department'),
                    session_id=session_data['id']
                )
                
                # Update session activity
                await self._update_session_activity(session_data['id'])
                
                return AuthSession(
                    is_valid=True,
                    user=auth_user,
                    session_id=session_data['id'],
                    expires_at=datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
                )
            
            return AuthSession(is_valid=False, error="Session not found or expired")
            
        except Exception as e:
            logger.debug(f"Custom session validation failed: {e}")
            return AuthSession(is_valid=False, error="Session validation failed")
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data from database"""
        try:
            result = self.client.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            return result.data if result.data else {}
            
        except Exception as e:
            logger.warning(f"Failed to get user profile for {user_id}: {e}")
            return {}
    
    async def _update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp"""
        try:
            self.client.table("user_sessions")\
                .update({
                    "last_activity_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", session_id)\
                .execute()
        except Exception as e:
            logger.warning(f"Failed to update session activity: {e}")
    
    async def validate_user_by_email(self, email: str) -> Optional[AuthUser]:
        """
        Get user information by email address
        Used for backward compatibility when only email is available
        """
        if not self.is_available:
            return None
        
        try:
            # Look up user by email in user_profiles
            # Note: We need to join with auth.users to get the email since it's not in user_profiles
            result = self.client.rpc('get_user_by_email', {'email_param': email}).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                
                return AuthUser(
                    id=user_data['id'],
                    email=email,
                    username=user_data.get('username'),
                    full_name=user_data.get('full_name'),
                    is_verified=user_data.get('is_verified', False),
                    role=user_data.get('role'),
                    department=user_data.get('department')
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to validate user by email {email}: {e}")
            return None
    
    async def create_anonymous_user_context(self, email: str) -> AuthUser:
        """
        Create a temporary user context for anonymous transactions
        Used when we only have email but no proper authentication
        """
        return AuthUser(
            id=f"anon_{email}",  # Temporary ID
            email=email,
            username=None,
            full_name=None,
            is_verified=False,
            role="anonymous"
        )
    
    async def log_user_activity(
        self, 
        user_id: str, 
        action: str, 
        resource: str = "transaction",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log user activity for audit trail"""
        if not self.is_available:
            return False
        
        try:
            self.client.table("user_activity_logs").insert({
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to log user activity: {e}")
            return False


# Global instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get the global auth service instance (lazy loaded)"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service 