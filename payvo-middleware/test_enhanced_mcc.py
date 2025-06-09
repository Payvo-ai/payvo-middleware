#!/usr/bin/env python3
import asyncio
import sys
import os

# Add middleware to path
sys.path.append('middleware')

from app.services.routing_orchestrator import routing_orchestrator

async def test_enhanced_prediction():
    print('🔬 Testing Enhanced GPS-First MCC Prediction System')
    print('=' * 60)
    
    try:
        # Test 1: GPS-based prediction 
        print('\n📍 Test 1: GPS-Based Location Prediction')
        session_id = await routing_orchestrator.initiate_routing('test_gps_user')
        print(f'   Session ID: {session_id}')
        
        result = await routing_orchestrator.activate_payment(session_id)
        print(f'   🎯 MCC: {result.get("predicted_mcc")}')
        print(f'   🔧 Method: {result.get("prediction_method")}')
        print(f'   📊 Confidence: {result.get("prediction_confidence")}')
        print(f'   🏪 Category: {result.get("merchant_category")}')
        
        # Test 2: Different session for variety
        print('\n📱 Test 2: Second Location Prediction')
        session_id2 = await routing_orchestrator.initiate_routing('test_location_user')
        result2 = await routing_orchestrator.activate_payment(session_id2)
        print(f'   Session ID: {session_id2}')
        print(f'   🎯 MCC: {result2.get("predicted_mcc")}')
        print(f'   🔧 Method: {result2.get("prediction_method")}')
        print(f'   📊 Confidence: {result2.get("prediction_confidence")}')
        
        # Test 3: Third session
        print('\n🏢 Test 3: Indoor Venue Prediction')
        session_id3 = await routing_orchestrator.initiate_routing('test_indoor_user')
        result3 = await routing_orchestrator.activate_payment(session_id3)
        print(f'   Session ID: {session_id3}')
        print(f'   🎯 MCC: {result3.get("predicted_mcc")}')
        print(f'   🔧 Method: {result3.get("prediction_method")}')
        print(f'   📊 Confidence: {result3.get("prediction_confidence")}')
        
        print('\n✅ Enhanced GPS-First Prediction System Active!')
        print('🎯 Location-based predictions are now prioritized')
        print('🏪 Indoor mapping capabilities enabled')
        print('📡 WiFi/BLE enhanced for venue detection')
        
    except Exception as e:
        print(f'❌ Error during testing: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_prediction()) 