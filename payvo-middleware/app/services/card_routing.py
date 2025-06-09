"""
Card Routing Engine
Selects optimal card based on MCC prediction and user preferences
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.schemas import (
    MCCPrediction, CardInfo, OptimalCardSelection, NetworkType
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class CardRoutingEngine:
    """
    Engine for selecting optimal card based on MCC and user preferences
    """
    
    def __init__(self):
        self.mcc_rewards_mapping = self._load_mcc_rewards_mapping()
        self.interchange_rates = self._load_interchange_rates()
        self.network_preferences = self._load_network_preferences()
    
    async def select_optimal_card(
        self, 
        user_id: str,
        mcc_prediction: MCCPrediction,
        available_cards: List[CardInfo],
        transaction_amount: Optional[float] = None
    ) -> OptimalCardSelection:
        """
        Select the optimal card for the predicted MCC
        """
        logger.info(f"Selecting optimal card for user {user_id}, MCC {mcc_prediction.mcc}")
        
        if not available_cards:
            raise ValueError("No cards available for selection")
        
        # Score each card for this MCC
        card_scores = []
        for card in available_cards:
            score = await self._score_card_for_mcc(
                card, mcc_prediction, transaction_amount
            )
            card_scores.append((card, score))
        
        # Sort by score (highest first)
        card_scores.sort(key=lambda x: x[1]["total_score"], reverse=True)
        
        best_card, best_score = card_scores[0]
        
        return OptimalCardSelection(
            card_id=best_card.card_id,
            network=best_card.network,
            selection_reason=best_score["reasoning"],
            expected_rewards=best_score.get("expected_rewards"),
            interchange_savings=best_score.get("interchange_savings"),
            confidence=min(mcc_prediction.confidence, best_score["confidence"])
        )
    
    async def _score_card_for_mcc(
        self, 
        card: CardInfo, 
        mcc_prediction: MCCPrediction,
        transaction_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Score a card for the given MCC prediction
        """
        mcc = mcc_prediction.mcc
        base_amount = transaction_amount or 100.0  # Default for calculation
        
        # Calculate rewards score
        rewards_score, expected_rewards = self._calculate_rewards_score(
            card, mcc, base_amount
        )
        
        # Calculate interchange score
        interchange_score, interchange_savings = self._calculate_interchange_score(
            card, mcc, base_amount
        )
        
        # Calculate network preference score
        network_score = self._calculate_network_score(card.network, mcc)
        
        # Calculate acceptance score (how widely accepted is this network)
        acceptance_score = self._calculate_acceptance_score(card.network)
        
        # Calculate card type preference score
        card_type_score = self._calculate_card_type_score(card.card_type, mcc)
        
        # Weighted total score
        weights = {
            "rewards": 0.4,
            "interchange": 0.2,
            "network": 0.15,
            "acceptance": 0.15,
            "card_type": 0.1
        }
        
        total_score = (
            rewards_score * weights["rewards"] +
            interchange_score * weights["interchange"] +
            network_score * weights["network"] +
            acceptance_score * weights["acceptance"] +
            card_type_score * weights["card_type"]
        )
        
        # Adjust score based on MCC prediction confidence
        confidence_multiplier = 0.5 + (mcc_prediction.confidence * 0.5)
        total_score *= confidence_multiplier
        
        reasoning_parts = []
        if rewards_score > 0.7:
            reasoning_parts.append(f"High rewards rate ({expected_rewards:.1f}%)")
        if interchange_score > 0.7:
            reasoning_parts.append("Low interchange fees")
        if network_score > 0.7:
            reasoning_parts.append(f"Preferred network for {self._get_mcc_category(mcc)}")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Best available option"
        
        return {
            "total_score": total_score,
            "rewards_score": rewards_score,
            "interchange_score": interchange_score,
            "network_score": network_score,
            "acceptance_score": acceptance_score,
            "card_type_score": card_type_score,
            "expected_rewards": expected_rewards,
            "interchange_savings": interchange_savings,
            "confidence": min(0.9, total_score),
            "reasoning": reasoning
        }
    
    def _calculate_rewards_score(
        self, 
        card: CardInfo, 
        mcc: str, 
        amount: float
    ) -> tuple[float, float]:
        """
        Calculate rewards score for this card and MCC
        """
        # Get card's rewards multiplier for this MCC
        multiplier = card.rewards_multiplier.get(mcc, 
                     card.rewards_multiplier.get("default", 1.0))
        
        # Get base rewards rate (assume 1% base)
        base_rate = 0.01
        effective_rate = base_rate * multiplier
        
        # Calculate expected rewards
        expected_rewards = amount * effective_rate
        rewards_percentage = effective_rate * 100
        
        # Score based on rewards rate (normalize to 0-1)
        # Excellent: 3%+, Good: 2%+, Average: 1%+, Poor: <1%
        if effective_rate >= 0.03:
            score = 1.0
        elif effective_rate >= 0.02:
            score = 0.8
        elif effective_rate >= 0.015:
            score = 0.6
        elif effective_rate >= 0.01:
            score = 0.4
        else:
            score = 0.2
        
        return score, rewards_percentage
    
    def _calculate_interchange_score(
        self, 
        card: CardInfo, 
        mcc: str, 
        amount: float
    ) -> tuple[float, float]:
        """
        Calculate interchange fee score
        """
        # Get interchange rate for this network and MCC
        network_rates = self.interchange_rates.get(card.network.value, {})
        interchange_rate = network_rates.get(mcc, network_rates.get("default", 0.02))
        
        # Calculate interchange cost
        interchange_cost = amount * interchange_rate
        
        # Score based on interchange rate (lower is better)
        # Excellent: <1.5%, Good: <2%, Average: <2.5%, Poor: 2.5%+
        if interchange_rate <= 0.015:
            score = 1.0
        elif interchange_rate <= 0.02:
            score = 0.8
        elif interchange_rate <= 0.025:
            score = 0.6
        else:
            score = 0.4
        
        return score, interchange_cost
    
    def _calculate_network_score(self, network: NetworkType, mcc: str) -> float:
        """
        Calculate network preference score for MCC
        """
        mcc_category = self._get_mcc_category(mcc)
        network_prefs = self.network_preferences.get(mcc_category, {})
        
        return network_prefs.get(network.value, 0.5)
    
    def _calculate_acceptance_score(self, network: NetworkType) -> float:
        """
        Calculate acceptance score based on network ubiquity
        """
        acceptance_rates = {
            NetworkType.VISA: 0.95,
            NetworkType.MASTERCARD: 0.93,
            NetworkType.AMEX: 0.75,
            NetworkType.DISCOVER: 0.65
        }
        
        return acceptance_rates.get(network, 0.5)
    
    def _calculate_card_type_score(self, card_type: str, mcc: str) -> float:
        """
        Calculate card type preference score for MCC
        """
        mcc_category = self._get_mcc_category(mcc)
        
        # Some MCCs prefer certain card types
        preferences = {
            "restaurants": {"credit": 0.8, "debit": 0.6, "prepaid": 0.4},
            "gas": {"credit": 0.9, "debit": 0.7, "prepaid": 0.5},
            "grocery": {"credit": 0.7, "debit": 0.8, "prepaid": 0.6},
            "retail": {"credit": 0.8, "debit": 0.7, "prepaid": 0.5}
        }
        
        category_prefs = preferences.get(mcc_category, {"credit": 0.7, "debit": 0.7, "prepaid": 0.5})
        return category_prefs.get(card_type.lower(), 0.5)
    
    def _get_mcc_category(self, mcc: str) -> str:
        """
        Map MCC to category for preference lookup
        """
        mcc_categories = {
            "5812": "restaurants",
            "5814": "restaurants", 
            "5411": "grocery",
            "5541": "gas",
            "5732": "retail",
            "5999": "retail",
            "5311": "retail",
            "5211": "retail"
        }
        
        return mcc_categories.get(mcc, "retail")
    
    def _load_mcc_rewards_mapping(self) -> Dict[str, Dict[str, float]]:
        """
        Load MCC to rewards multiplier mapping
        """
        # In production, this would be loaded from database
        return {
            "5812": {"amex": 3.0, "visa": 2.0, "mastercard": 2.0, "discover": 1.5},
            "5814": {"amex": 3.0, "visa": 2.0, "mastercard": 2.0, "discover": 1.5},
            "5411": {"amex": 2.0, "visa": 1.5, "mastercard": 1.5, "discover": 2.0},
            "5541": {"amex": 1.0, "visa": 3.0, "mastercard": 2.0, "discover": 2.0},
            "5732": {"amex": 2.0, "visa": 1.0, "mastercard": 1.0, "discover": 1.5},
            "default": {"amex": 1.0, "visa": 1.0, "mastercard": 1.0, "discover": 1.0}
        }
    
    def _load_interchange_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Load interchange rates by network and MCC
        """
        return {
            "visa": {
                "5812": 0.0195, "5814": 0.0195, "5411": 0.0175,
                "5541": 0.0165, "5732": 0.0185, "default": 0.018
            },
            "mastercard": {
                "5812": 0.0190, "5814": 0.0190, "5411": 0.0170,
                "5541": 0.0160, "5732": 0.0180, "default": 0.0175
            },
            "amex": {
                "5812": 0.0250, "5814": 0.0250, "5411": 0.0220,
                "5541": 0.0200, "5732": 0.0230, "default": 0.0225
            },
            "discover": {
                "5812": 0.0185, "5814": 0.0185, "5411": 0.0165,
                "5541": 0.0155, "5732": 0.0175, "default": 0.017
            }
        }
    
    def _load_network_preferences(self) -> Dict[str, Dict[str, float]]:
        """
        Load network preferences by merchant category
        """
        return {
            "restaurants": {
                "amex": 0.9, "visa": 0.8, "mastercard": 0.8, "discover": 0.6
            },
            "grocery": {
                "visa": 0.9, "mastercard": 0.9, "discover": 0.8, "amex": 0.7
            },
            "gas": {
                "visa": 0.9, "mastercard": 0.8, "discover": 0.8, "amex": 0.6
            },
            "retail": {
                "visa": 0.8, "mastercard": 0.8, "amex": 0.7, "discover": 0.7
            }
        }
    
    async def get_user_cards(self, user_id: str) -> List[CardInfo]:
        """
        Get user's available cards
        """
        # In production, this would query the database
        # For now, return mock data
        return [
            CardInfo(
                card_id="amex_gold_001",
                network=NetworkType.AMEX,
                last_four="1234",
                card_type="credit",
                issuer="American Express",
                rewards_multiplier={
                    "5812": 4.0,  # 4x on restaurants
                    "5814": 4.0,  # 4x on fast food
                    "5411": 2.0,  # 2x on grocery
                    "default": 1.0
                },
                interchange_fee=0.0225
            ),
            CardInfo(
                card_id="chase_sapphire_002", 
                network=NetworkType.VISA,
                last_four="5678",
                card_type="credit",
                issuer="Chase",
                rewards_multiplier={
                    "5812": 3.0,  # 3x on restaurants
                    "5814": 3.0,  # 3x on fast food
                    "default": 1.0
                },
                interchange_fee=0.018
            ),
            CardInfo(
                card_id="citi_double_cash_003",
                network=NetworkType.MASTERCARD,
                last_four="9012",
                card_type="credit", 
                issuer="Citi",
                rewards_multiplier={
                    "default": 2.0  # 2% on everything
                },
                interchange_fee=0.0175
            ),
            CardInfo(
                card_id="discover_it_004",
                network=NetworkType.DISCOVER,
                last_four="3456",
                card_type="credit",
                issuer="Discover",
                rewards_multiplier={
                    "5411": 5.0,  # 5% on grocery (rotating)
                    "5541": 5.0,  # 5% on gas (rotating)
                    "default": 1.0
                },
                interchange_fee=0.017
            )
        ]
    
    async def update_card_performance(
        self, 
        card_id: str, 
        mcc: str, 
        actual_rewards: float,
        transaction_success: bool
    ):
        """
        Update card performance metrics based on actual transaction results
        """
        logger.info(f"Updating performance for card {card_id}, MCC {mcc}")
        
        # In production, this would update database with:
        # - Actual rewards earned
        # - Transaction success rate
        # - Network acceptance rate
        # - User satisfaction scores
        
        pass


# Global instance
card_routing_engine = CardRoutingEngine() 