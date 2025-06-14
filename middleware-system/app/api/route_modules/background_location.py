from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

from app.database import get_db
from app.services.location_service import LocationService
from app.models.base import Base

router = APIRouter(prefix="/background-location", tags=["Background Location"])

# Database Models
class BackgroundLocationSession(Base):
    __tablename__ = "background_location_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    last_update = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    location_count = Column(Integer, default=0)
    metadata = Column(JSON, default={})

class BackgroundLocationPrediction(Base):
    __tablename__ = "background_location_predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    predicted_mcc = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    prediction_method = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    db: Session = Depends(get_db)
):
    """
    Start background location tracking session
    """
    try:
        # Generate unique session ID
        session_id = f"bg_session_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(minutes=request.session_duration_minutes)
        
        # Create session record
        session = BackgroundLocationSession(
            session_id=session_id,
            user_id=request.user_id,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
            is_active=True,
            expires_at=expires_at,
            location_count=0,
            metadata={
                "update_interval_seconds": request.update_interval_seconds,
                "min_distance_filter_meters": request.min_distance_filter_meters,
                "session_duration_minutes": request.session_duration_minutes
            }
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return BackgroundTrackingResponse(
            session_id=session_id,
            user_id=request.user_id,
            start_time=session.start_time,
            expires_at=session.expires_at,
            status="active",
            message="Background location tracking started successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start background tracking: {str(e)}")

@router.post("/update")
async def update_background_location(
    update: BackgroundLocationUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Update background location with MCC prediction
    """
    try:
        # Verify session exists and is active
        session = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.session_id == update.session_id,
            BackgroundLocationSession.is_active == True,
            BackgroundLocationSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Create location prediction record
        prediction = BackgroundLocationPrediction(
            session_id=update.session_id,
            user_id=update.user_id,
            latitude=update.location.latitude,
            longitude=update.location.longitude,
            accuracy=update.location.accuracy,
            predicted_mcc=update.mcc_prediction.mcc if update.mcc_prediction else None,
            confidence=update.mcc_prediction.confidence if update.mcc_prediction else None,
            prediction_method=update.mcc_prediction.method if update.mcc_prediction else None,
            timestamp=datetime.fromtimestamp(update.timestamp / 1000)  # Convert from milliseconds
        )
        
        db.add(prediction)
        
        # Update session
        session.last_update = datetime.utcnow()
        session.location_count += 1
        
        db.commit()
        
        # Schedule background processing if needed
        background_tasks.add_task(process_location_analytics, update.session_id, update.location)
        
        return {
            "status": "success",
            "message": "Location updated successfully",
            "session_id": update.session_id,
            "location_count": session.location_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update location: {str(e)}")

@router.get("/session/{session_id}/status", response_model=LocationSessionStatus)
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get background location session status
    """
    try:
        # Get session
        session = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get recent locations (last 10)
        recent_predictions = db.query(BackgroundLocationPrediction).filter(
            BackgroundLocationPrediction.session_id == session_id
        ).order_by(BackgroundLocationPrediction.timestamp.desc()).limit(10).all()
        
        recent_locations = []
        for pred in recent_predictions:
            recent_locations.append({
                "latitude": pred.latitude,
                "longitude": pred.longitude,
                "accuracy": pred.accuracy,
                "mcc": pred.predicted_mcc,
                "confidence": pred.confidence,
                "method": pred.prediction_method,
                "timestamp": pred.timestamp.isoformat()
            })
        
        return LocationSessionStatus(
            session_id=session.session_id,
            user_id=session.user_id,
            is_active=session.is_active and session.expires_at > datetime.utcnow(),
            start_time=session.start_time,
            last_update=session.last_update,
            expires_at=session.expires_at,
            location_count=session.location_count,
            recent_locations=recent_locations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.get("/session/{session_id}/optimal-mcc", response_model=OptimalMCCResponse)
async def get_optimal_mcc(
    session_id: str,
    current_lat: float = Field(..., ge=-90, le=90),
    current_lng: float = Field(..., ge=-180, le=180),
    radius_meters: int = Field(default=100, ge=10, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get optimal MCC prediction based on session history and current location
    """
    try:
        # Verify session exists
        session = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get recent predictions within radius and time window (last 10 minutes)
        time_threshold = datetime.utcnow() - timedelta(minutes=10)
        
        # Calculate distance using Haversine formula in SQL
        # This is a simplified version - for production, consider using PostGIS
        predictions = db.query(BackgroundLocationPrediction).filter(
            BackgroundLocationPrediction.session_id == session_id,
            BackgroundLocationPrediction.timestamp >= time_threshold,
            BackgroundLocationPrediction.predicted_mcc.isnot(None)
        ).all()
        
        if not predictions:
            raise HTTPException(status_code=404, detail="No recent predictions found")
        
        # Filter by distance and calculate weighted scores
        relevant_predictions = []
        for pred in predictions:
            distance = calculate_distance(
                current_lat, current_lng,
                pred.latitude, pred.longitude
            )
            
            if distance <= radius_meters:
                # Calculate weights based on distance, time, and confidence
                time_weight = max(0.1, 1 - (datetime.utcnow() - pred.timestamp).total_seconds() / 600)  # 10 minutes
                distance_weight = max(0.1, 1 - distance / radius_meters)
                confidence_weight = pred.confidence or 0.5
                
                total_weight = time_weight * distance_weight * confidence_weight
                
                relevant_predictions.append({
                    'mcc': pred.predicted_mcc,
                    'weight': total_weight,
                    'confidence': pred.confidence,
                    'method': pred.prediction_method,
                    'timestamp': pred.timestamp
                })
        
        if not relevant_predictions:
            raise HTTPException(status_code=404, detail="No relevant predictions found within radius")
        
        # Calculate weighted consensus
        mcc_scores = {}
        for pred in relevant_predictions:
            mcc = pred['mcc']
            if mcc not in mcc_scores:
                mcc_scores[mcc] = {'total_weight': 0, 'count': 0, 'max_confidence': 0}
            
            mcc_scores[mcc]['total_weight'] += pred['weight']
            mcc_scores[mcc]['count'] += 1
            mcc_scores[mcc]['max_confidence'] = max(mcc_scores[mcc]['max_confidence'], pred['confidence'])
        
        # Find best MCC
        best_mcc = None
        best_score = 0
        
        for mcc, data in mcc_scores.items():
            # Boost score for consensus (multiple predictions)
            consensus_boost = min(2.0, 1 + (data['count'] - 1) * 0.2)
            final_score = data['total_weight'] * consensus_boost
            
            if final_score > best_score:
                best_score = final_score
                best_mcc = mcc
        
        if not best_mcc:
            raise HTTPException(status_code=404, detail="Could not determine optimal MCC")
        
        # Calculate final confidence
        final_confidence = min(0.95, best_score / len(relevant_predictions))
        
        # Get session age and last prediction time
        session_age_minutes = int((datetime.utcnow() - session.start_time).total_seconds() / 60)
        last_prediction = max(relevant_predictions, key=lambda x: x['timestamp'])
        last_prediction_minutes_ago = int((datetime.utcnow() - last_prediction['timestamp']).total_seconds() / 60)
        
        return OptimalMCCResponse(
            mcc=best_mcc,
            confidence=final_confidence,
            method="background_session_consensus",
            location_count=len(relevant_predictions),
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
    additional_minutes: int = Field(default=30, ge=5, le=240),  # 5 minutes to 4 hours
    db: Session = Depends(get_db)
):
    """
    Extend background location session
    """
    try:
        session = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.session_id == session_id,
            BackgroundLocationSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found or inactive")
        
        # Extend expiration time
        session.expires_at = session.expires_at + timedelta(minutes=additional_minutes)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Session extended by {additional_minutes} minutes",
            "session_id": session_id,
            "new_expires_at": session.expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to extend session: {str(e)}")

@router.delete("/session/{session_id}")
async def stop_background_tracking(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Stop background location tracking session
    """
    try:
        session = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Mark session as inactive
        session.is_active = False
        db.commit()
        
        return {
            "status": "success",
            "message": "Background tracking stopped",
            "session_id": session_id,
            "final_location_count": session.location_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to stop tracking: {str(e)}")

@router.get("/sessions/user/{user_id}")
async def get_user_sessions(
    user_id: str,
    active_only: bool = False,
    limit: int = Field(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get background location sessions for a user
    """
    try:
        query = db.query(BackgroundLocationSession).filter(
            BackgroundLocationSession.user_id == user_id
        )
        
        if active_only:
            query = query.filter(
                BackgroundLocationSession.is_active == True,
                BackgroundLocationSession.expires_at > datetime.utcnow()
            )
        
        sessions = query.order_by(
            BackgroundLocationSession.start_time.desc()
        ).limit(limit).all()
        
        return {
            "user_id": user_id,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "start_time": s.start_time.isoformat(),
                    "last_update": s.last_update.isoformat(),
                    "expires_at": s.expires_at.isoformat(),
                    "is_active": s.is_active and s.expires_at > datetime.utcnow(),
                    "location_count": s.location_count,
                    "metadata": s.metadata
                }
                for s in sessions
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user sessions: {str(e)}")

# Background processing functions
async def process_location_analytics(session_id: str, location: LocationData):
    """
    Process location analytics in the background
    """
    try:
        # This could include:
        # - Pattern recognition
        # - Frequent location detection
        # - Route optimization
        # - Anomaly detection
        
        print(f"Processing analytics for session {session_id} at {location.latitude}, {location.longitude}")
        
        # Placeholder for advanced analytics
        await asyncio.sleep(0.1)  # Simulate processing
        
    except Exception as e:
        print(f"Analytics processing failed: {e}")

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in meters
    """
    import math
    
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c 