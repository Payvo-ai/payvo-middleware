from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import asyncio
import logging

from app.database import get_db
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/background-location", tags=["Background Location"])

# Request/Response Models
class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float = Field(..., gt=0)

class MCCPredictionData(BaseModel):
    mcc: str
    confidence: float = Field(..., ge=0, le=1)
    method: str
    timestamp: int

class BackgroundLocationUpdate(BaseModel):
    session_id: str
    user_id: str
    location: LocationData
    mcc_prediction: Optional[MCCPredictionData] = None
    timestamp: int

class StartBackgroundTrackingRequest(BaseModel):
    user_id: str
    session_duration_minutes: int = Field(default=30, ge=5, le=480)  # 5 minutes to 8 hours
    update_interval_seconds: int = Field(default=4, ge=1, le=60)  # 1 to 60 seconds
    min_distance_filter_meters: int = Field(default=5, ge=1, le=100)  # 1 to 100 meters

class BackgroundTrackingResponse(BaseModel):
    session_id: str
    user_id: str
    start_time: datetime
    expires_at: datetime
    status: str
    message: str

class LocationSessionStatus(BaseModel):
    session_id: str
    user_id: str
    is_active: bool
    start_time: datetime
    last_update: datetime
    expires_at: datetime
    location_count: int
    recent_locations: List[Dict[str, Any]]

class OptimalMCCResponse(BaseModel):
    mcc: str
    confidence: float
    method: str
    location_count: int
    session_age_minutes: int
    last_prediction_minutes_ago: int

# Initialize location service
location_service = LocationService()

@router.post("/start", response_model=BackgroundTrackingResponse)
async def start_background_tracking(
    request: StartBackgroundTrackingRequest,
    db = Depends(get_db)
):
    """
    Start background location tracking session
    """
    try:
        # Generate unique session ID
        session_id = f"bg_session_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(minutes=request.session_duration_minutes)
        
        # Create session record using Supabase
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        session_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "start_time": datetime.utcnow().isoformat(),
            "last_update": datetime.utcnow().isoformat(),
            "is_active": True,
            "expires_at": expires_at.isoformat(),
            "location_count": 0,
            "metadata": {
                "update_interval_seconds": request.update_interval_seconds,
                "min_distance_filter_meters": request.min_distance_filter_meters,
                "session_duration_minutes": request.session_duration_minutes
            }
        }
        
        # Store session in Supabase
        result = db.supabase_client.client.table("background_location_sessions").insert(session_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create tracking session")
        
        return BackgroundTrackingResponse(
            session_id=session_id,
            user_id=request.user_id,
            start_time=datetime.utcnow(),
            expires_at=expires_at,
            status="active",
            message="Background location tracking started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start background tracking: {str(e)}")

@router.post("/update")
async def update_background_location(
    update: BackgroundLocationUpdate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """
    Update background location with MCC prediction
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Verify session exists and is active
        session_result = db.supabase_client.client.table("background_location_sessions")\
            .select("*")\
            .eq("session_id", update.session_id)\
            .eq("is_active", True)\
            .gte("expires_at", datetime.utcnow().isoformat())\
            .execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        session = session_result.data[0]
        
        # Create location prediction record
        prediction_data = {
            "id": str(uuid.uuid4()),
            "session_id": update.session_id,
            "user_id": update.user_id,
            "latitude": update.location.latitude,
            "longitude": update.location.longitude,
            "accuracy": update.location.accuracy,
            "predicted_mcc": update.mcc_prediction.mcc if update.mcc_prediction else None,
            "confidence": update.mcc_prediction.confidence if update.mcc_prediction else None,
            "prediction_method": update.mcc_prediction.method if update.mcc_prediction else None,
            "timestamp": datetime.fromtimestamp(update.timestamp / 1000).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert prediction record
        db.supabase_client.client.table("background_location_predictions").insert(prediction_data).execute()
        
        # Update session
        updated_session_data = {
            "last_update": datetime.utcnow().isoformat(),
            "location_count": session["location_count"] + 1,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        db.supabase_client.client.table("background_location_sessions")\
            .update(updated_session_data)\
            .eq("session_id", update.session_id)\
            .execute()
        
        # Schedule background processing if needed
        background_tasks.add_task(process_location_analytics, update.session_id, update.location)
        
        return {
            "status": "success",
            "message": "Location updated successfully",
            "session_id": update.session_id,
            "location_count": session["location_count"] + 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update location: {str(e)}")

@router.get("/session/{session_id}/status", response_model=LocationSessionStatus)
async def get_session_status(
    session_id: str,
    db = Depends(get_db)
):
    """
    Get background location tracking session status
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get session data
        session_result = db.supabase_client.client.table("background_location_sessions")\
            .select("*")\
            .eq("session_id", session_id)\
            .execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = session_result.data[0]
        
        # Get recent locations
        locations_result = db.supabase_client.client.table("background_location_predictions")\
            .select("latitude, longitude, predicted_mcc, confidence, timestamp")\
            .eq("session_id", session_id)\
            .order("timestamp", desc=True)\
            .limit(10)\
            .execute()
        
        recent_locations = locations_result.data if locations_result.data else []
        
        return LocationSessionStatus(
            session_id=session["session_id"],
            user_id=session["user_id"],
            is_active=session["is_active"],
            start_time=datetime.fromisoformat(session["start_time"]),
            last_update=datetime.fromisoformat(session["last_update"]),
            expires_at=datetime.fromisoformat(session["expires_at"]),
            location_count=session["location_count"],
            recent_locations=recent_locations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.get("/session/{session_id}/optimal-mcc", response_model=OptimalMCCResponse)
async def get_optimal_mcc(
    session_id: str,
    current_lat: float = Query(..., ge=-90, le=90, description="Current latitude"),
    current_lng: float = Query(..., ge=-180, le=180, description="Current longitude"),
    radius_meters: int = Query(default=100, ge=10, le=1000, description="Search radius in meters"),
    db = Depends(get_db)
):
    """
    Get optimal MCC prediction based on session location history
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get session data
        session_result = db.supabase_client.client.table("background_location_sessions")\
            .select("*")\
            .eq("session_id", session_id)\
            .eq("is_active", True)\
            .execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Active session not found")
        
        session = session_result.data[0]
        
        # Get recent predictions within radius
        predictions_result = db.supabase_client.client.table("background_location_predictions")\
            .select("*")\
            .eq("session_id", session_id)\
            .not_.is_("predicted_mcc", "null")\
            .order("timestamp", desc=True)\
            .limit(50)\
            .execute()
        
        if not predictions_result.data:
            raise HTTPException(status_code=404, detail="No predictions found for session")
        
        # Filter predictions by distance and find the best one
        best_prediction = None
        best_confidence = 0
        
        for pred in predictions_result.data:
            distance = calculate_distance(
                current_lat, current_lng,
                pred["latitude"], pred["longitude"]
            )
            
            if distance <= radius_meters and pred["confidence"] > best_confidence:
                best_prediction = pred
                best_confidence = pred["confidence"]
        
        if not best_prediction:
            raise HTTPException(status_code=404, detail="No suitable predictions found within radius")
        
        # Calculate session age and last prediction time
        session_start = datetime.fromisoformat(session["start_time"])
        last_prediction_time = datetime.fromisoformat(best_prediction["timestamp"])
        
        session_age_minutes = int((datetime.utcnow() - session_start).total_seconds() / 60)
        last_prediction_minutes_ago = int((datetime.utcnow() - last_prediction_time).total_seconds() / 60)
        
        return OptimalMCCResponse(
            mcc=best_prediction["predicted_mcc"],
            confidence=best_prediction["confidence"],
            method=best_prediction["prediction_method"],
            location_count=session["location_count"],
            session_age_minutes=session_age_minutes,
            last_prediction_minutes_ago=last_prediction_minutes_ago
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimal MCC: {str(e)}")

@router.post("/session/{session_id}/extend")
async def extend_session(
    session_id: str,
    additional_minutes: int = Query(default=30, ge=5, le=240, description="Additional minutes to extend session"),
    db = Depends(get_db)
):
    """
    Extend background location tracking session
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get current session
        session_result = db.supabase_client.client.table("background_location_sessions")\
            .select("*")\
            .eq("session_id", session_id)\
            .eq("is_active", True)\
            .execute()
        
        if not session_result.data:
            raise HTTPException(status_code=404, detail="Active session not found")
        
        session = session_result.data[0]
        current_expires_at = datetime.fromisoformat(session["expires_at"])
        new_expires_at = current_expires_at + timedelta(minutes=additional_minutes)
        
        # Update session expiration
        update_data = {
            "expires_at": new_expires_at.isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        db.supabase_client.client.table("background_location_sessions")\
            .update(update_data)\
            .eq("session_id", session_id)\
            .execute()
        
        return {
            "status": "success",
            "message": f"Session extended by {additional_minutes} minutes",
            "session_id": session_id,
            "new_expires_at": new_expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extend session: {str(e)}")

@router.delete("/session/{session_id}")
async def stop_background_tracking(
    session_id: str,
    db = Depends(get_db)
):
    """
    Stop background location tracking session
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Update session to inactive
        update_data = {
            "is_active": False,
            "ended_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = db.supabase_client.client.table("background_location_sessions")\
            .update(update_data)\
            .eq("session_id", session_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "success",
            "message": "Background location tracking stopped",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop tracking: {str(e)}")

@router.get("/sessions/user/{user_id}")
async def get_user_sessions(
    user_id: str,
    active_only: bool = Query(default=False, description="Filter to active sessions only"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of sessions to return"),
    db = Depends(get_db)
):
    """
    Get user's background location tracking sessions
    """
    try:
        if not db.is_available:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Build query
        query = db.supabase_client.client.table("background_location_sessions")\
            .select("*")\
            .eq("user_id", user_id)
        
        if active_only:
            query = query.eq("is_active", True).gte("expires_at", datetime.utcnow().isoformat())
        
        result = query.order("start_time", desc=True).limit(limit).execute()
        
        return {
            "status": "success",
            "user_id": user_id,
            "sessions": result.data if result.data else [],
            "total_count": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user sessions: {str(e)}")

# Background processing functions
async def process_location_analytics(session_id: str, location: LocationData):
    """
    Process location analytics in the background
    """
    try:
        # This would typically involve:
        # 1. Analyzing location patterns
        # 2. Updating location-based caches
        # 3. Triggering ML model updates
        # 4. Generating insights
        
        # For now, just log the processing
        logger.info(f"Processing location analytics for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error processing location analytics: {str(e)}")

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in meters
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlng = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    
    return c * r 