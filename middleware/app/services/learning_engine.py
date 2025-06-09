"""
Learning & Feedback Engine for Payvo Middleware
Continuously improves MCC predictions and card routing decisions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict, deque

from app.models.schemas import (
    TransactionFeedback, MCCPrediction, RoutingDecision, 
    ContextData, CardInfo
)

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Machine learning engine that learns from transaction feedback
    to improve future MCC predictions and card routing decisions
    """
    
    def __init__(self):
        self.feedback_history = deque(maxlen=10000)  # Store recent feedback
        self.mcc_accuracy_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        self.card_performance_stats = defaultdict(lambda: {
            "success_rate": 0.0,
            "avg_rewards": 0.0,
            "transaction_count": 0,
            "decline_rate": 0.0
        })
        self.context_patterns = defaultdict(list)
        self.location_mcc_mapping = defaultdict(lambda: defaultdict(int))
        self.time_mcc_patterns = defaultdict(lambda: defaultdict(int))
        self.merchant_mcc_cache = {}
        
        # Learning parameters
        self.learning_rate = 0.1
        self.confidence_threshold = 0.7
        self.min_samples_for_learning = 10
        
        logger.info("Learning Engine initialized")
    
    async def process_feedback(self, feedback: TransactionFeedback) -> Dict:
        """
        Process transaction feedback to improve future predictions
        """
        try:
            # Store feedback
            self.feedback_history.append({
                "feedback": feedback,
                "timestamp": datetime.utcnow(),
                "processed": False
            })
            
            # Update MCC prediction accuracy
            await self._update_mcc_accuracy(feedback)
            
            # Update card performance metrics
            await self._update_card_performance(feedback)
            
            # Learn context patterns
            await self._learn_context_patterns(feedback)
            
            # Update location-MCC mappings
            await self._update_location_patterns(feedback)
            
            # Update time-based patterns
            await self._update_time_patterns(feedback)
            
            # Cache merchant information
            await self._update_merchant_cache(feedback)
            
            # Generate insights
            insights = await self._generate_insights(feedback)
            
            logger.info(f"Processed feedback for session {feedback.session_id}")
            
            return {
                "success": True,
                "insights": insights,
                "stats_updated": True
            }
            
        except Exception as e:
            logger.error(f"Feedback processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_mcc_accuracy(self, feedback: TransactionFeedback):
        """
        Update MCC prediction accuracy statistics
        """
        if feedback.actual_mcc and feedback.predicted_mcc:
            predicted_mcc = feedback.predicted_mcc
            actual_mcc = feedback.actual_mcc
            
            # Update overall accuracy
            self.mcc_accuracy_stats[predicted_mcc]["total"] += 1
            if predicted_mcc == actual_mcc:
                self.mcc_accuracy_stats[predicted_mcc]["correct"] += 1
            
            # Update category-level accuracy
            predicted_category = self._get_mcc_category(predicted_mcc)
            actual_category = self._get_mcc_category(actual_mcc)
            
            self.mcc_accuracy_stats[f"category_{predicted_category}"]["total"] += 1
            if predicted_category == actual_category:
                self.mcc_accuracy_stats[f"category_{predicted_category}"]["correct"] += 1
    
    async def _update_card_performance(self, feedback: TransactionFeedback):
        """
        Update card performance statistics
        """
        if feedback.selected_card_id:
            card_id = feedback.selected_card_id
            stats = self.card_performance_stats[card_id]
            
            # Update transaction count
            stats["transaction_count"] += 1
            
            # Update success rate
            if feedback.transaction_successful:
                success_count = stats["success_rate"] * (stats["transaction_count"] - 1) + 1
                stats["success_rate"] = success_count / stats["transaction_count"]
            else:
                success_count = stats["success_rate"] * (stats["transaction_count"] - 1)
                stats["success_rate"] = success_count / stats["transaction_count"]
            
            # Update decline rate
            if feedback.transaction_declined:
                decline_count = stats["decline_rate"] * (stats["transaction_count"] - 1) + 1
                stats["decline_rate"] = decline_count / stats["transaction_count"]
            else:
                decline_count = stats["decline_rate"] * (stats["transaction_count"] - 1)
                stats["decline_rate"] = decline_count / stats["transaction_count"]
            
            # Update average rewards
            if feedback.rewards_earned:
                total_rewards = stats["avg_rewards"] * (stats["transaction_count"] - 1) + feedback.rewards_earned
                stats["avg_rewards"] = total_rewards / stats["transaction_count"]
    
    async def _learn_context_patterns(self, feedback: TransactionFeedback):
        """
        Learn patterns from context data
        """
        if feedback.context_data and feedback.actual_mcc:
            context_key = self._create_context_signature(feedback.context_data)
            self.context_patterns[context_key].append({
                "mcc": feedback.actual_mcc,
                "timestamp": datetime.utcnow(),
                "success": feedback.transaction_successful
            })
            
            # Keep only recent patterns (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            self.context_patterns[context_key] = [
                pattern for pattern in self.context_patterns[context_key]
                if pattern["timestamp"] > cutoff_date
            ]
    
    async def _update_location_patterns(self, feedback: TransactionFeedback):
        """
        Update location-based MCC patterns
        """
        if (feedback.context_data and 
            feedback.context_data.location and 
            feedback.actual_mcc):
            
            location = feedback.context_data.location
            location_key = f"{location.latitude:.3f},{location.longitude:.3f}"
            self.location_mcc_mapping[location_key][feedback.actual_mcc] += 1
    
    async def _update_time_patterns(self, feedback: TransactionFeedback):
        """
        Update time-based MCC patterns
        """
        if feedback.actual_mcc and feedback.transaction_time:
            hour = feedback.transaction_time.hour
            day_of_week = feedback.transaction_time.weekday()
            
            time_key = f"{day_of_week}_{hour}"
            self.time_mcc_patterns[time_key][feedback.actual_mcc] += 1
    
    async def _update_merchant_cache(self, feedback: TransactionFeedback):
        """
        Cache merchant information for future predictions
        """
        if feedback.merchant_name and feedback.actual_mcc:
            self.merchant_mcc_cache[feedback.merchant_name.lower()] = {
                "mcc": feedback.actual_mcc,
                "confidence": min(1.0, self.merchant_mcc_cache.get(
                    feedback.merchant_name.lower(), {"confidence": 0}
                )["confidence"] + 0.1),
                "last_seen": datetime.utcnow()
            }
    
    async def _generate_insights(self, feedback: TransactionFeedback) -> Dict:
        """
        Generate actionable insights from feedback
        """
        insights = {
            "prediction_accuracy": await self._calculate_prediction_accuracy(),
            "card_recommendations": await self._generate_card_recommendations(),
            "pattern_discoveries": await self._discover_new_patterns(),
            "optimization_suggestions": await self._suggest_optimizations()
        }
        
        return insights
    
    async def _calculate_prediction_accuracy(self) -> Dict:
        """
        Calculate current prediction accuracy metrics
        """
        accuracy_metrics = {}
        
        for mcc_or_category, stats in self.mcc_accuracy_stats.items():
            if stats["total"] > 0:
                accuracy = stats["correct"] / stats["total"]
                accuracy_metrics[mcc_or_category] = {
                    "accuracy": accuracy,
                    "total_predictions": stats["total"],
                    "confidence": "high" if stats["total"] >= 50 else "medium" if stats["total"] >= 10 else "low"
                }
        
        return accuracy_metrics
    
    async def _generate_card_recommendations(self) -> List[Dict]:
        """
        Generate card performance recommendations
        """
        recommendations = []
        
        for card_id, stats in self.card_performance_stats.items():
            if stats["transaction_count"] >= 5:  # Minimum sample size
                recommendation = {
                    "card_id": card_id,
                    "performance_score": self._calculate_card_score(stats),
                    "strengths": [],
                    "weaknesses": []
                }
                
                # Identify strengths
                if stats["success_rate"] > 0.95:
                    recommendation["strengths"].append("High success rate")
                if stats["avg_rewards"] > 2.0:
                    recommendation["strengths"].append("High rewards earning")
                if stats["decline_rate"] < 0.05:
                    recommendation["strengths"].append("Low decline rate")
                
                # Identify weaknesses
                if stats["success_rate"] < 0.85:
                    recommendation["weaknesses"].append("Low success rate")
                if stats["decline_rate"] > 0.15:
                    recommendation["weaknesses"].append("High decline rate")
                if stats["avg_rewards"] < 1.0:
                    recommendation["weaknesses"].append("Low rewards earning")
                
                recommendations.append(recommendation)
        
        # Sort by performance score
        recommendations.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    async def _discover_new_patterns(self) -> List[Dict]:
        """
        Discover new patterns in the data
        """
        patterns = []
        
        # Location-based patterns
        for location, mcc_counts in self.location_mcc_mapping.items():
            if sum(mcc_counts.values()) >= 10:  # Minimum sample size
                most_common_mcc = max(mcc_counts, key=mcc_counts.get)
                confidence = mcc_counts[most_common_mcc] / sum(mcc_counts.values())
                
                if confidence > 0.7:  # High confidence pattern
                    patterns.append({
                        "type": "location",
                        "pattern": f"Location {location} strongly associated with MCC {most_common_mcc}",
                        "confidence": confidence,
                        "sample_size": sum(mcc_counts.values())
                    })
        
        # Time-based patterns
        for time_key, mcc_counts in self.time_mcc_patterns.items():
            if sum(mcc_counts.values()) >= 20:  # Minimum sample size
                most_common_mcc = max(mcc_counts, key=mcc_counts.get)
                confidence = mcc_counts[most_common_mcc] / sum(mcc_counts.values())
                
                if confidence > 0.6:  # Moderate confidence pattern
                    day_of_week, hour = time_key.split('_')
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    patterns.append({
                        "type": "temporal",
                        "pattern": f"{day_names[int(day_of_week)]} at {hour}:00 often involves MCC {most_common_mcc}",
                        "confidence": confidence,
                        "sample_size": sum(mcc_counts.values())
                    })
        
        return patterns
    
    async def _suggest_optimizations(self) -> List[Dict]:
        """
        Suggest system optimizations based on learned patterns
        """
        suggestions = []
        
        # Analyze prediction accuracy
        low_accuracy_mccs = []
        for mcc, stats in self.mcc_accuracy_stats.items():
            if not mcc.startswith("category_") and stats["total"] >= 10:
                accuracy = stats["correct"] / stats["total"]
                if accuracy < 0.6:
                    low_accuracy_mccs.append((mcc, accuracy, stats["total"]))
        
        if low_accuracy_mccs:
            suggestions.append({
                "type": "prediction_improvement",
                "description": "Focus on improving prediction accuracy for specific MCCs",
                "details": low_accuracy_mccs[:5],  # Top 5 problematic MCCs
                "priority": "high"
            })
        
        # Analyze card performance
        underperforming_cards = []
        for card_id, stats in self.card_performance_stats.items():
            if stats["transaction_count"] >= 10:
                score = self._calculate_card_score(stats)
                if score < 0.5:
                    underperforming_cards.append((card_id, score))
        
        if underperforming_cards:
            suggestions.append({
                "type": "card_optimization",
                "description": "Consider reviewing routing logic for underperforming cards",
                "details": underperforming_cards[:3],
                "priority": "medium"
            })
        
        return suggestions
    
    def _calculate_card_score(self, stats: Dict) -> float:
        """
        Calculate overall performance score for a card
        """
        success_weight = 0.4
        rewards_weight = 0.3
        decline_weight = 0.3
        
        # Normalize rewards (assuming max reasonable rewards is 5x)
        normalized_rewards = min(stats["avg_rewards"] / 5.0, 1.0)
        
        score = (
            stats["success_rate"] * success_weight +
            normalized_rewards * rewards_weight +
            (1 - stats["decline_rate"]) * decline_weight
        )
        
        return score
    
    def _create_context_signature(self, context: ContextData) -> str:
        """
        Create a signature for context data to identify patterns
        """
        signature_parts = []
        
        if context.location:
            # Round to ~100m precision
            lat = round(context.location.latitude, 3)
            lon = round(context.location.longitude, 3)
            signature_parts.append(f"loc_{lat}_{lon}")
        
        if context.wifi_networks:
            # Use top 2 strongest networks
            sorted_networks = sorted(
                context.wifi_networks, 
                key=lambda x: x.signal_strength, 
                reverse=True
            )[:2]
            for network in sorted_networks:
                signature_parts.append(f"wifi_{network.ssid}")
        
        if context.bluetooth_devices:
            # Use device types
            device_types = set(device.device_type for device in context.bluetooth_devices)
            for device_type in sorted(device_types):
                signature_parts.append(f"ble_{device_type}")
        
        return "_".join(signature_parts) if signature_parts else "unknown"
    
    def _get_mcc_category(self, mcc: str) -> str:
        """
        Get category for MCC code
        """
        mcc_categories = {
            "5812": "restaurants",
            "5814": "restaurants", 
            "5411": "grocery",
            "5541": "gas",
            "5732": "electronics",
            "5999": "retail"
        }
        return mcc_categories.get(mcc, "other")
    
    async def get_learning_insights(self) -> Dict:
        """
        Get current learning insights and statistics
        """
        return {
            "total_feedback_processed": len(self.feedback_history),
            "mcc_accuracy_stats": dict(self.mcc_accuracy_stats),
            "card_performance_stats": dict(self.card_performance_stats),
            "patterns_discovered": len(self.context_patterns),
            "location_mappings": len(self.location_mcc_mapping),
            "merchant_cache_size": len(self.merchant_mcc_cache),
            "learning_health": await self._assess_learning_health()
        }
    
    async def _assess_learning_health(self) -> Dict:
        """
        Assess the health of the learning system
        """
        total_feedback = len(self.feedback_history)
        recent_feedback = sum(
            1 for entry in self.feedback_history
            if (datetime.utcnow() - entry["timestamp"]).days <= 7
        )
        
        return {
            "status": "healthy" if total_feedback > 100 else "learning",
            "total_samples": total_feedback,
            "recent_activity": recent_feedback,
            "data_quality": "good" if recent_feedback > 10 else "limited"
        }


# Global learning engine instance
learning_engine = LearningEngine() 