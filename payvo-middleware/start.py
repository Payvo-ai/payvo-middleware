#!/usr/bin/env python3
"""
Robust startup script for Payvo Middleware
Handles initialization and graceful error handling for cloud deployment
"""

import os
import sys
import time
import logging
import asyncio
import uvicorn
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_app_startup():
    """Test if the application can start up properly"""
    try:
        logger.info("🧪 Testing app imports...")
        from app.main import app
        logger.info("✅ FastAPI app imported successfully")
        
        # Test basic imports without initialization
        from app.services.routing_orchestrator import routing_orchestrator
        logger.info("✅ Routing orchestrator imported successfully")
        
        # Test config import
        from app.core.config import settings
        logger.info(f"✅ Configuration loaded - Debug: {settings.DEBUG}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Startup test failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False

async def test_minimal_initialization():
    """Test minimal initialization without blocking operations"""
    try:
        logger.info("🔧 Testing minimal initialization...")
        from app.services.routing_orchestrator import routing_orchestrator
        
        # Only test that we can access the orchestrator, don't initialize
        logger.info(f"✅ Orchestrator accessible - Running: {routing_orchestrator.is_running}")
        
        # Test database connection availability (don't connect)
        from app.database.connection_manager import connection_manager
        logger.info(f"✅ Connection manager accessible")
        
        return True
    except Exception as e:
        logger.error(f"❌ Minimal initialization test failed: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting Payvo Middleware...")
    
    # Get configuration from environment with Railway-specific handling
    railway_port = os.getenv("PORT")  # Railway sets this
    payvo_port = os.getenv("PAYVO_PORT")
    
    # Railway uses PORT, fallback to PAYVO_PORT, then default
    if railway_port:
        port = int(railway_port)
        logger.info(f"🚂 Using Railway PORT: {port}")
    elif payvo_port:
        port = int(payvo_port)
        logger.info(f"🔧 Using PAYVO_PORT: {port}")
    else:
        port = 8000
        logger.info(f"📌 Using default port: {port}")
    
    host = os.getenv("PAYVO_HOST", "0.0.0.0")
    debug = os.getenv("PAYVO_DEBUG", "false").lower() == "true"
    
    logger.info(f"📡 Final configuration: host={host}, port={port}, debug={debug}")
    logger.info(f"🔧 All environment variables: PORT={os.getenv('PORT')}, PAYVO_PORT={os.getenv('PAYVO_PORT')}, PAYVO_HOST={os.getenv('PAYVO_HOST')}")
    
    # Validate port
    if port < 1 or port > 65535:
        logger.error(f"❌ Invalid port: {port}")
        sys.exit(1)
    
    # Test startup with timeout
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test basic imports with timeout
        logger.info("🔍 Phase 1: Testing basic imports...")
        startup_success = loop.run_until_complete(
            asyncio.wait_for(test_app_startup(), timeout=30.0)
        )
        
        if not startup_success:
            logger.error("❌ Failed basic import tests")
            sys.exit(1)
        
        # Test minimal initialization with timeout
        logger.info("🔍 Phase 2: Testing minimal initialization...")
        init_success = loop.run_until_complete(
            asyncio.wait_for(test_minimal_initialization(), timeout=15.0)
        )
        
        if not init_success:
            logger.warning("⚠️ Minimal initialization had issues, but continuing...")
        
    except asyncio.TimeoutError:
        logger.error("❌ Startup tests timed out - continuing anyway...")
    except Exception as e:
        logger.error(f"❌ Startup test exception: {e}")
        logger.warning("⚠️ Continuing startup despite test failures...")
    finally:
        loop.close()
    
    logger.info("✅ Pre-startup tests completed")
    logger.info("🏪 Enhanced GPS-First MCC Prediction System Active!")
    logger.info("📱 Ready for payment routing requests")
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"🔗 Health check will be available at: http://{host}:{port}/api/v1/health")
    
    # Start the server with robust configuration
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info" if not debug else "debug",
            workers=1,  # Single worker for Railway
            timeout_keep_alive=30,  # Keep connections alive
            timeout_graceful_shutdown=30  # Graceful shutdown timeout
        )
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 