"""
Payvo Middleware - Advanced MCC-based Card Routing System
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uvicorn
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.routes import router
from app.services.routing_orchestrator import routing_orchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Payvo Middleware...")
    
    try:
        # Initialize services
        await routing_orchestrator.initialize()
        logger.info("✅ Routing orchestrator initialized")
        
        # Start background tasks
        await routing_orchestrator.start_background_tasks()
        logger.info("✅ Background tasks started")
        
        logger.info("Payvo Middleware started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Payvo Middleware: {e}")
        # Don't fail startup - just log the error and continue
        logger.warning("⚠️ Continuing startup without full initialization")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Payvo Middleware...")
    
    try:
        # Stop background tasks
        await routing_orchestrator.stop_background_tasks()
        
        # Cleanup resources
        await routing_orchestrator.cleanup()
        
        logger.info("Payvo Middleware shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")
        # Continue with shutdown anyway


# Create FastAPI application
app = FastAPI(
    title="Payvo Middleware",
    description="Advanced MCC-based Card Routing System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add security middleware
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=settings.ALLOWED_HOSTS
# )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests with timing information
    """
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"Path: {request.url.path}"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {e} - Time: {process_time:.3f}s")
        raise


# Rate limiting middleware (basic implementation)
request_counts = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """
    Basic rate limiting middleware
    """
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    request_counts[client_ip] = [
        timestamp for timestamp in request_counts.get(client_ip, [])
        if current_time - timestamp < 60
    ]
    
    # Check rate limit
    if len(request_counts.get(client_ip, [])) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Add current request
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    request_counts[client_ip].append(current_time)
    
    response = await call_next(request)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with system information
    """
    return {
        "service": "Payvo Middleware",
        "version": "1.0.0",
        "description": "Advanced MCC-based Card Routing System",
        "status": "operational",
        "endpoints": {
            "health": "/api/v1/health",
            "docs": "/docs" if settings.DEBUG else "disabled",
            "metrics": "/api/v1/metrics"
        }
    }


# Additional system endpoints
@app.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancer health checks
    """
    return {"status": "ok", "timestamp": time.time()}


@app.get("/version")
async def version():
    """
    Version information endpoint
    """
    return {
        "version": "1.0.0",
        "build": "production",
        "features": [
            "MCC Prediction Engine",
            "Card Routing Optimization", 
            "Token Provisioning",
            "Learning & Feedback Loop",
            "Privacy-First Architecture"
        ]
    }


if __name__ == "__main__":
    # Get port from environment variable for cloud deployment
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting Payvo Middleware on {host}:{port}")
    print(f"📡 Enhanced GPS-First MCC Prediction System Active!")
    print(f"🏪 Indoor mapping capabilities enabled")
    print(f"📱 Ready for payment routing requests")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        access_log=True,
        log_level="info"
    ) 