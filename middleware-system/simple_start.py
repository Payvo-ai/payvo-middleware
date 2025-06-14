#!/usr/bin/env python3
"""
Simple startup script for Railway debugging
"""

import os
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get port from Railway
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"🚀 Simple start: {host}:{port}")
    logger.info(f"📦 PORT env var: {os.getenv('PORT')}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        raise

if __name__ == "__main__":
    main() 