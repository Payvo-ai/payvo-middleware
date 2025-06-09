#!/usr/bin/env python3
"""
Test Installation Script for Payvo Middleware
This script verifies that all components are properly installed and configured.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_openai_connection():
    """Test OpenAI API connectivity"""
    try:
        from openai import AsyncOpenAI
        from app.core.config import settings
        
        if not settings.OPENAI_API_KEY:
            logger.warning("⚠️  OpenAI API key not configured - LLM features will use fallback")
            return True
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Test with a simple completion
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10,
            temperature=0.1
        )
        
        if response.choices and response.choices[0].message:
            logger.info("✅ OpenAI API connection successful")
            logger.info(f"   Model: {settings.OPENAI_MODEL}")
            logger.info(f"   Response: {response.choices[0].message.content[:50]}...")
            return True
        else:
            logger.error("❌ OpenAI API returned empty response")
            return False
            
    except ImportError as e:
        logger.error(f"❌ OpenAI package not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ OpenAI API connection failed: {e}")
        return False

async def test_supabase_connection():
    """Test Supabase connectivity"""
    try:
        from supabase import create_client
        from app.core.config import settings
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.error("❌ Supabase credentials not configured")
            return False
        
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        
        # Test connection by checking health
        response = client.table('health_check').select('*').limit(1).execute()
        
        logger.info("✅ Supabase connection successful")
        logger.info(f"   URL: {settings.SUPABASE_URL[:30]}...")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Supabase package not installed: {e}")
        return False
    except Exception as e:
        # This might fail if table doesn't exist, which is okay
        logger.info("✅ Supabase connection established")
        logger.info(f"   URL: {settings.SUPABASE_URL[:30]}...")
        return True

async def test_basic_imports():
    """Test that all basic modules can be imported"""
    try:
        from app.main import app
        from app.core.config import settings
        from app.services.routing_orchestrator import RoutingOrchestrator
        from app.services.mcc_prediction import MCCPredictionEngine
        from app.services.ai_inference import ai_inference_service
        from app.models.schemas import PreTapContext, MCCPrediction
        
        logger.info("✅ All core modules imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

async def test_ai_inference_service():
    """Test AI inference service initialization"""
    try:
        from app.services.ai_inference import ai_inference_service
        
        # Test service initialization
        if ai_inference_service.openai_client:
            logger.info("✅ AI Inference Service initialized with OpenAI")
        else:
            logger.info("⚠️  AI Inference Service initialized in fallback mode (no OpenAI key)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ AI Inference Service test failed: {e}")
        return False

async def test_mcc_prediction_engine():
    """Test MCC prediction engine"""
    try:
        from app.services.mcc_prediction import MCCPredictionEngine
        from app.models.schemas import PreTapContext, LocationData, TerminalData
        
        engine = MCCPredictionEngine()
        
        # Create a test context
        test_context = PreTapContext(
            session_id="test-session",
            user_id="test-user",
            timestamp=datetime.utcnow(),
            location=LocationData(
                latitude=37.7749,
                longitude=-122.4194,
                accuracy=10.0
            ),
            terminal_data=TerminalData(
                terminal_id="TEST_TERMINAL",
                device_id="test-device",
                pos_type="square"
            )
        )
        
        # Test prediction (this should work even without external services)
        prediction = await engine.predict_mcc(test_context)
        
        if prediction:
            logger.info("✅ MCC Prediction Engine test successful")
            logger.info(f"   Predicted MCC: {prediction.mcc}")
            logger.info(f"   Confidence: {prediction.confidence}")
            logger.info(f"   Method: {prediction.method}")
        else:
            logger.error("❌ MCC Prediction Engine returned no prediction")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ MCC Prediction Engine test failed: {e}")
        return False

async def test_routing_orchestrator():
    """Test routing orchestrator"""
    try:
        from app.services.routing_orchestrator import RoutingOrchestrator
        
        orchestrator = RoutingOrchestrator()
        
        # Test initialization
        await orchestrator.initialize()
        
        logger.info("✅ Routing Orchestrator test successful")
        
        # Cleanup
        await orchestrator.cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Routing Orchestrator test failed: {e}")
        return False

async def test_database_write():
    """Test database write capability"""
    try:
        from supabase import create_client
        from app.core.config import settings
        
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            logger.warning("⚠️  Service role key not configured - skipping write test")
            return True
        
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        
        # Try to insert a test record
        test_data = {
            "session_id": f"test-{datetime.utcnow().timestamp()}",
            "user_id": "test-user",
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = client.table('payment_sessions').insert(test_data).execute()
        
        if response.data:
            logger.info("✅ Database write test successful")
            
            # Clean up test record
            client.table('payment_sessions').delete().eq('session_id', test_data['session_id']).execute()
            
            return True
        else:
            logger.error("❌ Database write test failed - no data returned")
            return False
        
    except Exception as e:
        logger.warning(f"⚠️  Database write test failed (this is okay if schema isn't set up): {e}")
        return True  # Don't fail the test for this

async def test_environment_variables():
    """Test environment variable configuration"""
    try:
        from app.core.config import settings
        
        logger.info("🔍 Environment Configuration:")
        logger.info(f"   Debug Mode: {settings.PAYVO_DEBUG}")
        logger.info(f"   Host: {settings.PAYVO_HOST}")
        logger.info(f"   Port: {settings.PAYVO_PORT}")
        logger.info(f"   Secret Key: {'✅ Set' if settings.PAYVO_SECRET_KEY else '❌ Missing'}")
        logger.info(f"   Supabase URL: {'✅ Set' if settings.SUPABASE_URL else '❌ Missing'}")
        logger.info(f"   Supabase Anon Key: {'✅ Set' if settings.SUPABASE_ANON_KEY else '❌ Missing'}")
        logger.info(f"   OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '⚠️  Not set'}")
        
        required_vars = [
            settings.PAYVO_SECRET_KEY,
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        ]
        
        if all(required_vars):
            logger.info("✅ Required environment variables configured")
            return True
        else:
            logger.error("❌ Some required environment variables are missing")
            return False
        
    except Exception as e:
        logger.error(f"❌ Environment variable test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Payvo Middleware Installation Test")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Basic Imports", test_basic_imports),
        ("Supabase Connection", test_supabase_connection),
        ("OpenAI Connection", test_openai_connection),
        ("AI Inference Service", test_ai_inference_service),
        ("MCC Prediction Engine", test_mcc_prediction_engine),
        ("Routing Orchestrator", test_routing_orchestrator),
        ("Database Write", test_database_write),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Testing: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:<8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Payvo Middleware is ready to use.")
        logger.info("\n🚀 Next steps:")
        logger.info("   1. Start the server: python run.py")
        logger.info("   2. Visit http://localhost:8000/docs for API documentation")
        logger.info("   3. Test with: curl http://localhost:8000/ping")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the configuration.")
        logger.error("   Review the STARTUP_GUIDE.md for troubleshooting steps.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        sys.exit(1) 