"""
Authentication Middleware for Payvo Middleware System
Handles request authentication, user context injection, and session validation
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import Request, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.auth_service import get_auth_service, AuthUser, AuthSession

logger = logging.getLogger(__name__)

# Security scheme for FastAPI docs
security = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates authentication on protected routes
    Injects user context into request state
    """
    
    def __init__(self, app, protected_paths: Optional[list] = None):
        super().__init__(app)
        self.auth_service = get_auth_service()
        
        # Paths that require authentication
        self.protected_paths = protected_paths or [
            "/api/v1/transactions",
            "/api/v1/balance",
            "/api/v1/history",
            "/api/v1/user",
            "/api/v1/accounts"
        ]
        
        # Paths that are excluded from authentication
        self.excluded_paths = [
            "/docs", "/redoc", "/openapi.json",
            "/health", "/status",
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/predict-mcc", "/api/v1/prediction",
            "/api/v1/feedback", "/api/v1/transaction-feedback"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request authentication"""
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Initialize user context
        request.state.user = None
        request.state.is_authenticated = False
        request.state.auth_session = None
        
        # Check if this is a protected path
        is_protected = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        # Extract authentication token
        auth_token = await self._extract_auth_token(request)
        
        if auth_token:
            # Validate the token
            auth_session = await self.auth_service.validate_session_token(auth_token)
            
            if auth_session.is_valid and auth_session.user:
                # Set authenticated user context
                request.state.user = auth_session.user
                request.state.is_authenticated = True
                request.state.auth_session = auth_session
                
                # Log successful authentication
                logger.info(f"✅ User authenticated: {auth_session.user.email} ({auth_session.user.id})")
                
                # Log user activity for protected resources
                if is_protected:
                    await self.auth_service.log_user_activity(
                        user_id=auth_session.user.id,
                        action=f"{request.method} {request.url.path}",
                        resource="api_access",
                        metadata={
                            "method": request.method,
                            "path": request.url.path,
                            "query_params": dict(request.query_params),
                            "user_agent": request.headers.get("user-agent"),
                            "ip_address": request.client.host if request.client else None
                        }
                    )
            else:
                logger.warning(f"❌ Authentication failed: {auth_session.error}")
                
                # If this is a protected path, return 401
                if is_protected:
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "error": "Authentication required",
                            "message": auth_session.error or "Invalid or expired token",
                            "code": "AUTH_FAILED"
                        }
                    )
        
        elif is_protected:
            # No token provided for protected path
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Authentication required",
                    "message": "No authentication token provided",
                    "code": "NO_AUTH_TOKEN"
                }
            )
        
        # Continue with the request
        return await call_next(request)
    
    async def _extract_auth_token(self, request: Request) -> Optional[str]:
        """Extract authentication token from request"""
        
        # Try Authorization header first (Bearer token)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Try X-Auth-Token header
        auth_token_header = request.headers.get("x-auth-token")
        if auth_token_header:
            return auth_token_header
        
        # Try query parameter (for webhooks or special cases)
        auth_token_param = request.query_params.get("auth_token")
        if auth_token_param:
            return auth_token_param
        
        # Try session token in cookies (for web interface)
        session_token = request.cookies.get("session_token")
        if session_token:
            return session_token
        
        return None


async def get_current_user(request: Request) -> Optional[AuthUser]:
    """
    Dependency function to get the current authenticated user
    Use this in your API endpoints to access user information
    """
    return getattr(request.state, 'user', None)


async def get_current_user_required(request: Request) -> AuthUser:
    """
    Dependency function that requires authentication
    Raises 401 if no authenticated user
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Authentication required",
                "message": "This endpoint requires authentication",
                "code": "AUTH_REQUIRED"
            }
        )
    return user


async def require_role(required_roles: list) -> Callable:
    """
    Dependency factory for role-based access control
    """
    async def role_checker(request: Request) -> AuthUser:
        user = await get_current_user_required(request)
        
        if user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Insufficient permissions",
                    "message": f"This endpoint requires one of the following roles: {', '.join(required_roles)}",
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "required_roles": required_roles,
                    "user_role": user.role
                }
            )
        
        return user
    
    return role_checker


class AuthContext:
    """
    Context manager for authentication operations
    Provides easy access to user information and authentication state
    """
    
    def __init__(self, request: Request):
        self.request = request
        self.user = getattr(request.state, 'user', None)
        self.is_authenticated = getattr(request.state, 'is_authenticated', False)
        self.auth_session = getattr(request.state, 'auth_session', None)
    
    @property
    def user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self.user.id if self.user else None
    
    @property
    def user_email(self) -> Optional[str]:
        """Get current user email"""
        return self.user.email if self.user else None
    
    @property
    def user_role(self) -> Optional[str]:
        """Get current user role"""
        return self.user.role if self.user else None
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return self.user_role == role if self.user_role else False
    
    def has_any_role(self, roles: list) -> bool:
        """Check if user has any of the specified roles"""
        return self.user_role in roles if self.user_role else False
    
    async def log_activity(self, action: str, resource: str = "transaction", metadata: Optional[Dict[str, Any]] = None):
        """Log user activity"""
        if self.user:
            auth_service = get_auth_service()
            await auth_service.log_user_activity(
                user_id=self.user.id,
                action=action,
                resource=resource,
                metadata=metadata
            )


def get_auth_context(request: Request) -> AuthContext:
    """Get authentication context for current request"""
    return AuthContext(request)


# Helper functions for backwards compatibility
async def authenticate_user_by_email(email: str) -> Optional[AuthUser]:
    """
    Authenticate user by email for backwards compatibility
    This should be replaced with proper token-based auth
    """
    auth_service = get_auth_service()
    user = await auth_service.validate_user_by_email(email)
    
    if not user:
        # Create anonymous user context for transactions
        user = await auth_service.create_anonymous_user_context(email)
    
    return user


async def create_transaction_context(user_email: str) -> Dict[str, Any]:
    """
    Create transaction context with user information
    Used by transaction processors to include user data
    """
    user = await authenticate_user_by_email(user_email)
    
    return {
        "user_id": user.id if user else None,
        "user_email": user_email,
        "user_role": user.role if user else "anonymous",
        "is_authenticated": user.role != "anonymous" if user else False,
        "timestamp": datetime.utcnow().isoformat()
    } 