"""
Authentication API endpoints for Payvo Middleware
Handles authentication-related operations and user session management
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request, Depends, Body
from pydantic import BaseModel, EmailStr

from app.services.auth_service import get_auth_service, AuthUser, AuthSession
from app.middleware.auth_middleware import (
    get_current_user, 
    get_current_user_required, 
    get_auth_context,
    create_transaction_context
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])


# Request/Response Models
class TokenValidationRequest(BaseModel):
    """Request model for token validation"""
    token: str


class TokenValidationResponse(BaseModel):
    """Response model for token validation"""
    is_valid: bool
    user: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_verified: bool = False
    role: Optional[str] = None
    department: Optional[str] = None
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None


class SessionInfoResponse(BaseModel):
    """Response model for session information"""
    session_id: Optional[str] = None
    user_id: str
    is_authenticated: bool
    expires_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class UserLookupRequest(BaseModel):
    """Request model for user lookup by email"""
    email: EmailStr


class TransactionContextRequest(BaseModel):
    """Request model for creating transaction context"""
    user_email: EmailStr
    transaction_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/auth/validate-token", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """
    Validate an authentication token (JWT or session token)
    Used by mobile app to verify if tokens are still valid
    """
    try:
        auth_service = get_auth_service()
        
        if not auth_service.is_available:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Authentication service unavailable",
                    "message": "Unable to validate tokens at this time",
                    "code": "AUTH_SERVICE_UNAVAILABLE"
                }
            )
        
        # Validate the token
        auth_session = await auth_service.validate_session_token(request.token)
        
        if auth_session.is_valid and auth_session.user:
            return TokenValidationResponse(
                is_valid=True,
                user={
                    "id": auth_session.user.id,
                    "email": auth_session.user.email,
                    "username": auth_session.user.username,
                    "full_name": auth_session.user.full_name,
                    "is_verified": auth_session.user.is_verified,
                    "role": auth_session.user.role,
                    "department": auth_session.user.department
                },
                session_id=auth_session.session_id,
                expires_at=auth_session.expires_at
            )
        else:
            return TokenValidationResponse(
                is_valid=False,
                error=auth_session.error or "Invalid or expired token"
            )
    
    except Exception as e:
        logger.error(f"❌ Token validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Token validation failed",
                "message": str(e),
                "code": "VALIDATION_ERROR"
            }
        )


@router.get("/auth/profile", response_model=UserProfileResponse)
async def get_user_profile(
    request: Request,
    current_user: AuthUser = Depends(get_current_user_required)
):
    """
    Get current authenticated user profile
    Requires valid authentication token
    """
    try:
        auth_context = get_auth_context(request)
        
        # Log profile access
        await auth_context.log_activity(
            action="profile_access",
            resource="user_profile",
            metadata={"endpoint": "/auth/profile"}
        )
        
        return UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            full_name=current_user.full_name,
            is_verified=current_user.is_verified,
            role=current_user.role,
            department=current_user.department
        )
    
    except Exception as e:
        logger.error(f"❌ Profile access failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Profile access failed",
                "message": str(e),
                "code": "PROFILE_ERROR"
            }
        )


@router.get("/auth/session", response_model=SessionInfoResponse)
async def get_session_info(
    request: Request,
    current_user: AuthUser = Depends(get_current_user_required)
):
    """
    Get current session information
    Provides session details and activity status
    """
    try:
        auth_context = get_auth_context(request)
        
        return SessionInfoResponse(
            session_id=auth_context.auth_session.session_id if auth_context.auth_session else None,
            user_id=current_user.id,
            is_authenticated=auth_context.is_authenticated,
            expires_at=auth_context.auth_session.expires_at if auth_context.auth_session else None,
            last_activity=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"❌ Session info access failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Session access failed",
                "message": str(e),
                "code": "SESSION_ERROR"
            }
        )


@router.post("/auth/lookup-user")
async def lookup_user_by_email(request: UserLookupRequest):
    """
    Look up user information by email address
    Used for backwards compatibility with transaction processing
    """
    try:
        auth_service = get_auth_service()
        
        if not auth_service.is_available:
            # Return anonymous user context if auth service unavailable
            user = await auth_service.create_anonymous_user_context(request.email)
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "is_authenticated": False
                },
                "message": "User context created (auth service unavailable)"
            }
        
        # Try to find existing user
        user = await auth_service.validate_user_by_email(request.email)
        
        if user and user.role != "anonymous":
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "is_verified": user.is_verified,
                    "role": user.role,
                    "department": user.department,
                    "is_authenticated": True
                },
                "message": "User found"
            }
        else:
            # Create anonymous user context
            anon_user = await auth_service.create_anonymous_user_context(request.email)
            return {
                "success": True,
                "user": {
                    "id": anon_user.id,
                    "email": anon_user.email,
                    "role": anon_user.role,
                    "is_authenticated": False
                },
                "message": "Anonymous user context created"
            }
    
    except Exception as e:
        logger.error(f"❌ User lookup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "User lookup failed",
                "message": str(e),
                "code": "LOOKUP_ERROR"
            }
        )


@router.post("/auth/transaction-context")
async def create_transaction_user_context(request: TransactionContextRequest):
    """
    Create user context for transaction processing
    Provides backwards compatibility for existing transaction flows
    """
    try:
        # Create transaction context with user information
        context = await create_transaction_context(request.user_email)
        
        # Add additional metadata if provided
        if request.metadata:
            context["metadata"] = request.metadata
        
        if request.transaction_id:
            context["transaction_id"] = request.transaction_id
        
        # Log transaction context creation
        if context.get("user_id") and context["user_id"] != f"anon_{request.user_email}":
            auth_service = get_auth_service()
            await auth_service.log_user_activity(
                user_id=context["user_id"],
                action="transaction_context_created",
                resource="transaction",
                metadata={
                    "transaction_id": request.transaction_id,
                    "user_email": request.user_email,
                    "is_authenticated": context["is_authenticated"]
                }
            )
        
        return {
            "success": True,
            "context": context,
            "message": "Transaction context created successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Transaction context creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Context creation failed",
                "message": str(e),
                "code": "CONTEXT_ERROR"
            }
        )


@router.get("/auth/status")
async def get_auth_status(request: Request):
    """
    Get authentication service status and capabilities
    """
    try:
        auth_service = get_auth_service()
        current_user = await get_current_user(request)
        
        return {
            "success": True,
            "data": {
                "auth_service_available": auth_service.is_available,
                "is_authenticated": current_user is not None,
                "user_id": current_user.id if current_user else None,
                "user_email": current_user.email if current_user else None,
                "user_role": current_user.role if current_user else None,
                "timestamp": datetime.utcnow().isoformat()
            },
            "message": "Authentication status retrieved successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Auth status check failed: {e}")
        return {
            "success": False,
            "data": {
                "auth_service_available": False,
                "is_authenticated": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            "error": str(e),
            "message": "Authentication status check failed"
        }


@router.post("/auth/activity-log")
async def log_user_activity(
    request: Request,
    activity_data: Dict[str, Any] = Body(...),
    current_user: AuthUser = Depends(get_current_user_required)
):
    """
    Log user activity for audit trail
    Allows clients to log important user actions
    """
    try:
        auth_context = get_auth_context(request)
        
        # Extract activity data
        action = activity_data.get("action", "unknown_action")
        resource = activity_data.get("resource", "user_activity")
        metadata = activity_data.get("metadata", {})
        
        # Add request metadata
        metadata.update({
            "endpoint": "/auth/activity-log",
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Log the activity
        success = await auth_context.log_activity(
            action=action,
            resource=resource,
            metadata=metadata
        )
        
        if success:
            return {
                "success": True,
                "message": "Activity logged successfully",
                "activity": {
                    "user_id": current_user.id,
                    "action": action,
                    "resource": resource,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to log activity",
                "error": "Activity logging service unavailable"
            }
    
    except Exception as e:
        logger.error(f"❌ Activity logging failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Activity logging failed",
                "message": str(e),
                "code": "ACTIVITY_LOG_ERROR"
            }
        ) 