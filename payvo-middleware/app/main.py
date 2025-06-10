"""
FastAPI application setup with enhanced lifespan management
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Enhanced lifespan manager with timeout handling and graceful degradation
    """
    logger.info("🚀 Starting Payvo Middleware lifespan...")
    
    # Startup phase with timeout and error handling
    try:
        logger.info("📡 Initializing routing orchestrator...")
        
        # Import and initialize with timeout
        async def init_with_timeout():
            from app.services.routing_orchestrator import routing_orchestrator
            
            # Initialize orchestrator with timeout
            if not routing_orchestrator.is_running:
                logger.info("🔧 Initializing routing orchestrator...")
                await routing_orchestrator.initialize()
                logger.info("✅ Routing orchestrator initialized successfully")
            else:
                logger.info("ℹ️ Routing orchestrator already running")
            
            # Start background tasks with timeout
            logger.info("⚙️ Starting background tasks...")
            await routing_orchestrator.start_background_tasks()
            logger.info("✅ Background tasks started successfully")
            
            return True
        
        # Run initialization with timeout
        try:
            success = await asyncio.wait_for(init_with_timeout(), timeout=45.0)
            if success:
                logger.info("✅ All services initialized successfully")
        except asyncio.TimeoutError:
            logger.warning("⚠️ Service initialization timed out - continuing with partial initialization")
        except Exception as e:
            logger.warning(f"⚠️ Service initialization failed: {e}")
            logger.warning("⚠️ Continuing startup in degraded mode...")
    
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        logger.warning("⚠️ Continuing startup with minimal services...")
    
    logger.info("✅ Lifespan startup completed")
    
    # Yield control to the application
    yield
    
    # Shutdown phase with timeout and error handling
    logger.info("🛑 Starting graceful shutdown...")
    
    try:
        async def shutdown_with_timeout():
            from app.services.routing_orchestrator import routing_orchestrator
            
            # Stop background tasks
            logger.info("⏹️ Stopping background tasks...")
            await routing_orchestrator.stop_background_tasks()
            logger.info("✅ Background tasks stopped")
            
            # Cleanup routing orchestrator
            logger.info("⏹️ Cleaning up routing orchestrator...")
            await routing_orchestrator.cleanup()
            logger.info("✅ Routing orchestrator cleanup completed")
            
            return True
        
        # Run shutdown with timeout
        try:
            await asyncio.wait_for(shutdown_with_timeout(), timeout=30.0)
            logger.info("✅ Graceful shutdown completed")
        except asyncio.TimeoutError:
            logger.warning("⚠️ Shutdown timed out - forcing exit")
        except Exception as e:
            logger.warning(f"⚠️ Shutdown error: {e} - forcing exit")
            
    except Exception as e:
        logger.error(f"❌ Critical shutdown error: {e}")
    
    logger.info("🏁 Lifespan shutdown completed")

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="Payvo Middleware",
    description="Enhanced GPS-First MCC Prediction System for Payment Routing",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Payvo Middleware API",
        "version": "2.0.0",
        "status": "active",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }

@app.get("/health")
async def simple_health():
    """Simple health check endpoint for basic monitoring"""
    return {"status": "healthy", "service": "payvo-middleware"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 