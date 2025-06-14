#!/usr/bin/env python3
"""
Payvo Middleware Startup Script
Runs the complete Payvo Middleware application with all services
"""

import asyncio
import logging
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Payvo Middleware"""
    try:
        logger.info("🚀 Starting Payvo Middleware...")
        
        # Import after path setup
        from app.core.config import settings
        
        logger.info(f"📡 Server Configuration:")
        logger.info(f"   Host: {settings.HOST}")
        logger.info(f"   Port: {settings.PORT}")
        logger.info(f"   Debug: {settings.DEBUG}")
        logger.info(f"   Supabase: {'✅ Configured' if settings.use_supabase else '❌ Not configured'}")
        
        logger.info(f"🌐 Access your application at:")
        logger.info(f"   Main: http://{settings.HOST}:{settings.PORT}")
        if settings.DEBUG:
            logger.info(f"   Docs: http://{settings.HOST}:{settings.PORT}/docs")
            logger.info(f"   Health: http://{settings.HOST}:{settings.PORT}/api/v1/health")
        
        # Run the server using import string
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            log_level="info" if settings.DEBUG else "warning",
            reload=settings.DEBUG,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 