#!/usr/bin/env python3
"""
Real Transaction Simulator for Payvo Middleware
Simulates realistic payment terminal data to test MCC prediction accuracy
"""

import asyncio
import json
import requests
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class RealTransactionSimulator:
    """Simulates realistic payment terminal interactions"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Payvo-Transaction-Simulator/1.0'
        })
        
        # Real-world merchant data with known MCCs
        self.real_merchants = [
            {
                "name": "McDonald's",
                "terminal_id": "MCD_SQUARE_001",
                "actual_mcc": "5814",  # Fast Food
                "location": {"lat": 37.7749, "lng": -122.4194},
                "typical_amount_range": (5.50, 15.99),
                "pos_type": "square",
                "merchant_category": "fast_food"
            },
            {
                "name": "Whole Foods Market",
                "terminal_id": "WFM_TERM_001", 
                "actual_mcc": "5411",  # Grocery
                "location": {"lat": 37.7849, "lng": -122.4094},
                "typical_amount_range": (25.00, 150.00),
                "pos_type": "verifone",
                "merchant_category": "grocery"
            },
            {
                "name": "Shell Gas Station",
                "terminal_id": "SHELL_POS_001",
                "actual_mcc": "5542",  # Gas Station
                "location": {"lat": 37.7649, "lng": -122.4294},
                "typical_amount_range": (30.00, 80.00),
                "pos_type": "gilbarco",
                "merchant_category": "gas_station"
            },
            {
                "name": "The Cheesecake Factory",
                "terminal_id": "TCF_CLOVER_001",
                "actual_mcc": "5812",  # Restaurant
                "location": {"lat": 37.7949, "lng": -122.3994},
                "typical_amount_range": (45.00, 120.00),
                "pos_type": "clover",
                "merchant_category": "restaurant"
            },
            {
                "name": "CVS Pharmacy",
                "terminal_id": "CVS_NCR_001",
                "actual_mcc": "5912",  # Drug Store
                "location": {"lat": 37.7549, "lng": -122.4394},
                "typical_amount_range": (8.00, 45.00),
                "pos_type": "ncr",
                "merchant_category": "pharmacy"
            },
            {
                "name": "Starbucks Coffee",
                "terminal_id": "SBUX_SQUARE_001",
                "actual_mcc": "5814",  # Fast Food/Coffee
                "location": {"lat": 37.7749, "lng": -122.4094},
                "typical_amount_range": (4.50, 12.99),
                "pos_type": "square",
                "merchant_category": "coffee"
            },
            {
                "name": "Target",
                "terminal_id": "TGT_VERIFONE_001",
                "actual_mcc": "5310",  # Discount Store
                "location": {"lat": 37.7849, "lng": -122.4194},
                "typical_amount_range": (15.00, 89.99),
                "pos_type": "verifone",
                "merchant_category": "retail"
            },
            {
                "name": "Best Buy",
                "terminal_id": "BBY_INGENICO_001",
                "actual_mcc": "5732",  # Electronics
                "location": {"lat": 37.7649, "lng": -122.4094},
                "typical_amount_range": (99.00, 899.99),
                "pos_type": "ingenico",
                "merchant_category": "electronics"
            }
        ]
        
        # User cards for testing routing
        self.test_cards = [
            {
                "card_id": "visa_sapphire",
                "network": "visa",
                "rewards_rate": 0.02,
                "mcc_bonuses": {"5812": 0.03, "5814": 0.03}  # Dining bonus
            },
            {
                "card_id": "amex_gold",
                "network": "amex", 
                "rewards_rate": 0.01,
                "mcc_bonuses": {"5411": 0.04, "5814": 0.04}  # Groceries & Dining
            },
            {
                "card_id": "chase_freedom",
                "network": "visa",
                "rewards_rate": 0.015,
                "mcc_bonuses": {"5542": 0.05}  # Gas station bonus
            }
        ]
    
    def get_time_context(self) -> Dict[str, str]:
        """Generate realistic time context"""
        now = datetime.now()
        
        # Determine time of day
        hour = now.hour
        if 6 <= hour < 11:
            time_of_day = "morning"
        elif 11 <= hour < 14:
            time_of_day = "lunch"
        elif 14 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Day of week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_of_week = days[now.weekday()]
        
        return {
            "time_of_day": time_of_day,
            "day_of_week": day_of_week,
            "hour": hour
        }
    
    def simulate_transaction_flow(self, merchant: Dict, user_id: str = None) -> Dict[str, Any]:
        """Simulate a complete transaction flow from pre-tap to feedback"""
        
        if not user_id:
            user_id = f"user_{random.randint(1000, 9999)}"
        
        session_id = str(uuid.uuid4())
        time_context = self.get_time_context()
        transaction_amount = round(random.uniform(*merchant["typical_amount_range"]), 2)
        
        print(f"\n🏪 Simulating transaction at: {merchant['name']}")
        print(f"   💰 Amount: ${transaction_amount}")
        print(f"   🕐 Time: {time_context['time_of_day']} on {time_context['day_of_week']}")
        
        # Step 1: Pre-tap MCC Prediction
        prediction_request = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "location": {
                "latitude": merchant["location"]["lat"] + random.uniform(-0.001, 0.001),
                "longitude": merchant["location"]["lng"] + random.uniform(-0.001, 0.001),
                "accuracy": random.uniform(5.0, 15.0)
            },
            "terminal_data": {
                "terminal_id": merchant["terminal_id"],
                "device_id": f"device_{random.randint(100, 999)}",
                "pos_type": merchant["pos_type"]
            },
            "context_features": {
                "time_of_day": time_context["time_of_day"],
                "day_of_week": time_context["day_of_week"],
                "merchant_category": merchant["merchant_category"]
            }
        }
        
        # Make MCC prediction
        prediction_response = self.session.post(f"{API_BASE}/predict-mcc", json=prediction_request)
        
        if prediction_response.status_code != 200:
            print(f"   ❌ MCC Prediction failed: {prediction_response.status_code}")
            return {"error": "MCC prediction failed"}
        
        prediction_data = prediction_response.json().get('data', {})
        predicted_mcc = prediction_data.get('mcc')
        prediction_confidence = prediction_data.get('confidence', 0.0)
        prediction_method = prediction_data.get('method', 'unknown')
        
        print(f"   🧠 Predicted MCC: {predicted_mcc} (confidence: {prediction_confidence:.2f})")
        print(f"   🎯 Actual MCC: {merchant['actual_mcc']}")
        
        # Check prediction accuracy
        is_accurate = predicted_mcc == merchant['actual_mcc']
        accuracy_emoji = "✅" if is_accurate else "❌"
        print(f"   {accuracy_emoji} Prediction accuracy: {'CORRECT' if is_accurate else 'INCORRECT'}")
        
        # Step 2: Card Routing
        routing_request = {
            "session_id": session_id,
            "user_id": user_id,
            "predicted_mcc": predicted_mcc,
            "transaction_amount": transaction_amount,
            "user_cards": self.test_cards,
            "location": {
                "latitude": merchant["location"]["lat"],
                "longitude": merchant["location"]["lng"]
            }
        }
        
        routing_response = self.session.post(f"{API_BASE}/route-card", json=routing_request)
        
        if routing_response.status_code != 200:
            print(f"   ❌ Card Routing failed: {routing_response.status_code}")
            return {"error": "Card routing failed"}
        
        routing_data = routing_response.json().get('data', {})
        selected_card = routing_data.get('recommended_card_id')
        expected_rewards = routing_data.get('expected_rewards', 0.0)
        
        print(f"   💳 Selected card: {selected_card}")
        print(f"   💰 Expected rewards: ${expected_rewards:.4f}")
        
        # Step 3: Simulate transaction execution
        time.sleep(1)  # Simulate processing time
        
        # Simulate transaction success/failure (95% success rate)
        transaction_success = random.random() < 0.95
        
        # Calculate actual rewards based on actual MCC
        selected_card_data = next(card for card in self.test_cards if card['card_id'] == selected_card)
        actual_rewards_rate = selected_card_data['mcc_bonuses'].get(merchant['actual_mcc'], selected_card_data['rewards_rate'])
        actual_rewards = transaction_amount * actual_rewards_rate if transaction_success else 0.0
        
        print(f"   🔄 Transaction: {'SUCCESS' if transaction_success else 'FAILED'}")
        print(f"   💎 Actual rewards: ${actual_rewards:.4f}")
        
        # Step 4: Send transaction feedback
        feedback_data = {
            "session_id": session_id,
            "user_id": user_id,
            "predicted_mcc": predicted_mcc,
            "actual_mcc": merchant['actual_mcc'],
            "prediction_confidence": prediction_confidence,
            "prediction_method": prediction_method,
            "selected_card_id": selected_card,
            "network_used": selected_card_data['network'],
            "transaction_success": transaction_success,
            "rewards_earned": actual_rewards,
            "merchant_name": merchant['name'],
            "transaction_amount": transaction_amount,
            "location_lat": merchant["location"]["lat"],
            "location_lng": merchant["location"]["lng"]
        }
        
        feedback_response = self.session.post(f"{API_BASE}/transaction-feedback", json=feedback_data)
        
        if feedback_response.status_code != 200:
            print(f"   ❌ Feedback submission failed: {feedback_response.status_code}")
        else:
            print(f"   📊 Feedback submitted successfully")
        
        return {
            "session_id": session_id,
            "merchant": merchant['name'],
            "predicted_mcc": predicted_mcc,
            "actual_mcc": merchant['actual_mcc'],
            "accurate": is_accurate,
            "confidence": prediction_confidence,
            "method": prediction_method,
            "transaction_amount": transaction_amount,
            "rewards_earned": actual_rewards,
            "transaction_success": transaction_success
        }
    
    def run_simulation_suite(self, num_transactions: int = 20):
        """Run a comprehensive simulation of multiple transactions"""
        print("🚀 Starting Payvo Middleware Transaction Simulation")
        print("=" * 70)
        
        results = []
        
        for i in range(num_transactions):
            print(f"\n📋 Transaction {i+1}/{num_transactions}")
            
            # Select random merchant
            merchant = random.choice(self.real_merchants)
            
            # Simulate transaction
            result = self.simulate_transaction_flow(merchant)
            
            if 'error' not in result:
                results.append(result)
            
            # Small delay between transactions
            time.sleep(0.5)
        
        # Calculate statistics
        print("\n" + "=" * 70)
        print("📈 SIMULATION RESULTS")
        print("=" * 70)
        
        if results:
            total_transactions = len(results)
            accurate_predictions = sum(1 for r in results if r['accurate'])
            accuracy_rate = accurate_predictions / total_transactions
            
            total_rewards = sum(r['rewards_earned'] for r in results)
            successful_transactions = sum(1 for r in results if r['transaction_success'])
            success_rate = successful_transactions / total_transactions
            
            print(f"📊 Total Transactions: {total_transactions}")
            print(f"🎯 MCC Prediction Accuracy: {accuracy_rate:.2%} ({accurate_predictions}/{total_transactions})")
            print(f"✅ Transaction Success Rate: {success_rate:.2%} ({successful_transactions}/{total_transactions})")
            print(f"💰 Total Rewards Earned: ${total_rewards:.2f}")
            print(f"💳 Average Rewards per Transaction: ${total_rewards/total_transactions:.2f}")
            
            # Breakdown by merchant category
            print(f"\n📋 Accuracy by Merchant Category:")
            categories = {}
            for result in results:
                merchant_info = next(m for m in self.real_merchants if m['actual_mcc'] == result['actual_mcc'])
                category = merchant_info['merchant_category']
                if category not in categories:
                    categories[category] = {'total': 0, 'accurate': 0}
                categories[category]['total'] += 1
                if result['accurate']:
                    categories[category]['accurate'] += 1
            
            for category, stats in categories.items():
                accuracy = stats['accurate'] / stats['total']
                print(f"   {category}: {accuracy:.2%} ({stats['accurate']}/{stats['total']})")
        
        print("\n🎉 Simulation completed!")
        return results


def main():
    """Main simulation runner"""
    print("Payvo Middleware Real Transaction Simulator")
    print("Testing MCC prediction accuracy with realistic merchant data")
    print()
    
    simulator = RealTransactionSimulator()
    
    # Run simulation
    num_transactions = int(input("How many transactions to simulate? (default: 10): ") or "10")
    results = simulator.run_simulation_suite(num_transactions)
    
    # Offer to check analytics
    print(f"\n💡 Check real-time analytics at: {BASE_URL}/api/v1/analytics")
    print(f"📚 View API documentation at: {BASE_URL}/docs")


if __name__ == "__main__":
    main() 