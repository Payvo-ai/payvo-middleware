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
        
        # Test that we can import core services
        try:
            from app.services.llm_service import LLMService
            logger.info("✅ LLM service importable")
        except Exception as e:
            logger.warning(f"⚠️ LLM service import issue: {e}")
        
        try:
            from app.core.config import settings
            logger.info(f"✅ Settings accessible - OpenAI key: {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
        except Exception as e:
            logger.warning(f"⚠️ Settings access issue: {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Minimal initialization test failed: {e}")
        import traceback
        logger.error(f"❌ Minimal init traceback: {traceback.format_exc()}")
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
        try:
            startup_success = loop.run_until_complete(
                asyncio.wait_for(test_app_startup(), timeout=30.0)
            )
            
            if not startup_success:
                logger.error("❌ Failed basic import tests")
                logger.error("❌ This indicates critical import or dependency issues")
                # Don't exit - continue to see what specific error occurs
            else:
                logger.info("✅ Basic imports successful")
        except Exception as e:
            logger.error(f"❌ Import test exception: {e}")
            import traceback
            logger.error(f"❌ Import traceback: {traceback.format_exc()}")
        
        # Test minimal initialization with timeout
        logger.info("🔍 Phase 2: Testing minimal initialization...")
        try:
            init_success = loop.run_until_complete(
                asyncio.wait_for(test_minimal_initialization(), timeout=15.0)
            )
            
            if not init_success:
                logger.warning("⚠️ Minimal initialization had issues, but continuing...")
            else:
                logger.info("✅ Minimal initialization successful")
        except Exception as e:
            logger.error(f"❌ Initialization test exception: {e}")
            import traceback
            logger.error(f"❌ Initialization traceback: {traceback.format_exc()}")
        
    except asyncio.TimeoutError:
        logger.error("❌ Startup tests timed out - continuing anyway...")
    except Exception as e:
        logger.error(f"❌ Startup test exception: {e}")
        import traceback
        logger.error(f"❌ Startup test traceback: {traceback.format_exc()}")
        logger.warning("⚠️ Continuing startup despite test failures...")
    finally:
        loop.close()
    
    logger.info("✅ Pre-startup tests completed")
    logger.info("🏪 Enhanced GPS-First MCC Prediction System Active!")
    logger.info("📱 Ready for payment routing requests")
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"🔗 Health check will be available at: http://{host}:{port}/api/v1/health")
    
    # Log environment variables for debugging
    logger.info(f"🔧 Environment debug:")
    logger.info(f"   PORT={os.getenv('PORT')}")
    logger.info(f"   PAYVO_PORT={os.getenv('PAYVO_PORT')}")
    logger.info(f"   PAYVO_HOST={os.getenv('PAYVO_HOST')}")
    logger.info(f"   OPENAI_API_KEY={'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    logger.info(f"   SUPABASE_URL={'SET' if os.getenv('SUPABASE_URL') else 'NOT SET'}")
    
    # Start the server with robust configuration
    try:
        logger.info("🚀 Attempting to start uvicorn server...")
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
        
        # Try to identify the specific issue
        if "Address already in use" in str(e):
            logger.error(f"❌ Port {port} is already in use")
        elif "Permission denied" in str(e):
            logger.error(f"❌ Permission denied for port {port}")
        elif "Cannot assign requested address" in str(e):
            logger.error(f"❌ Cannot bind to address {host}:{port}")
        else:
            logger.error(f"❌ Unknown server startup error: {type(e).__name__}")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 