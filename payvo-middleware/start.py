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
        from app.main import app
        logger.info("✅ FastAPI app imported successfully")
        
        # Test basic imports
        from app.services.routing_orchestrator import routing_orchestrator
        logger.info("✅ Routing orchestrator imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Startup test failed: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("🚀 Starting Payvo Middleware...")
    
    # Get configuration from environment
    host = os.getenv("PAYVO_HOST", "0.0.0.0")
    port = int(os.getenv("PAYVO_PORT", os.getenv("PORT", 8000)))
    debug = os.getenv("PAYVO_DEBUG", "false").lower() == "true"
    
    logger.info(f"📡 Configuration: host={host}, port={port}, debug={debug}")
    logger.info(f"🔧 Environment variables: PORT={os.getenv('PORT')}, PAYVO_PORT={os.getenv('PAYVO_PORT')}")
    
    # Validate port
    if port < 1 or port > 65535:
        logger.error(f"❌ Invalid port: {port}")
        sys.exit(1)
    
    # Test startup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    startup_success = loop.run_until_complete(test_app_startup())
    loop.close()
    
    if not startup_success:
        logger.error("❌ Failed to initialize application")
        sys.exit(1)
    
    logger.info("✅ Pre-startup tests passed")
    logger.info("🏪 Enhanced GPS-First MCC Prediction System Active!")
    logger.info("📱 Ready for payment routing requests")
    logger.info(f"🌐 Starting server on {host}:{port}")
    
    # Start the server
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info" if not debug else "debug",
            workers=1  # Single worker for Railway
        )
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 