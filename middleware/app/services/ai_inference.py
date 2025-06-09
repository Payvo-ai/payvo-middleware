"""
AI Inference Service for LLM-based MCC prediction using OpenAI
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIInferenceService:
    """
    Service for AI-powered MCC inference using OpenAI GPT models
    """
    
    def __init__(self):
        self.openai_client = None
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        else:
            logger.warning("OpenAI API key not found - LLM features will use fallback")
    
    async def predict_mcc(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Predict MCC using OpenAI GPT models
        """
        try:
            # Try OpenAI first
            if self.openai_client:
                result = await self._predict_with_openai(context)
                if result:
                    return result
            
            # Fallback to rule-based inference if OpenAI fails
            logger.warning("OpenAI not available, using rule-based fallback")
            return self._rule_based_fallback(context)
            
        except Exception as e:
            logger.error(f"AI inference failed: {e}")
            return self._rule_based_fallback(context)
    
    async def predict_merchant_category(self, merchant_name: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Predict merchant category and MCC based on merchant name using OpenAI
        """
        try:
            if not self.openai_client:
                return None
                
            prompt = self._create_merchant_prediction_prompt(merchant_name, context)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use GPT-4o-mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": self._get_merchant_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI merchant prediction failed: {e}")
            return None
    
    async def analyze_transaction_context(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze transaction context for insights using OpenAI
        """
        try:
            if not self.openai_client:
                return None
                
            prompt = self._create_context_analysis_prompt(context)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_context_analysis_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"OpenAI context analysis failed: {e}")
            return None
    
    async def _predict_with_openai(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI GPT for MCC prediction
        """
        try:
            prompt = self._create_mcc_prompt(context)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model for MCC prediction
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = self._parse_llm_response(content)
            
            if result:
                result["llm_model"] = "gpt-4o-mini"
                result["llm_provider"] = "openai"
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI prediction failed: {e}")
            return None
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for MCC prediction
        """
        return """You are an expert in merchant category codes (MCCs) for payment processing. 

Your task is to predict the most likely 4-digit MCC based on contextual information about a transaction.

Common MCCs:
- 5814: Fast Food Restaurants
- 5812: Eating Places, Restaurants  
- 5411: Grocery Stores, Supermarkets
- 5732: Electronics Stores
- 5999: Miscellaneous Retail
- 5541: Service Stations (Gas)
- 5311: Department Stores
- 5211: Lumber/Building Materials
- 4111: Transportation/Subway/Commuter
- 7011: Hotels, Motels
- 5542: Automated Fuel Dispensers
- 5921: Package Stores - Beer, Wine, Liquor
- 7832: Motion Picture Theaters
- 5691: Men's and Women's Clothing
- 5661: Shoe Stores

Respond with a JSON object containing:
- "mcc": 4-digit MCC code (string)
- "confidence": confidence score 0.0-1.0 (number)
- "reasoning": brief explanation (string)
- "category": general category name (string)

Example: {"mcc": "5814", "confidence": 0.85, "reasoning": "Morning time and mobile POS suggests coffee shop or fast food", "category": "fast_food"}"""
    
    def _get_merchant_system_prompt(self) -> str:
        """
        System prompt for merchant category prediction
        """
        return """You are an expert in merchant categorization and MCC codes.

Given a merchant name, predict the most appropriate MCC code and category.

Respond with a JSON object containing:
- "mcc": 4-digit MCC code (string)
- "confidence": confidence score 0.0-1.0 (number)
- "reasoning": brief explanation (string)
- "category": general category name (string)
- "merchant_type": specific type of business (string)

Example: {"mcc": "5812", "confidence": 0.95, "reasoning": "Pizza Hut is a well-known restaurant chain", "category": "restaurant", "merchant_type": "pizza_restaurant"}"""
    
    def _get_context_analysis_system_prompt(self) -> str:
        """
        System prompt for transaction context analysis
        """
        return """You are an expert in analyzing payment transaction contexts to extract insights.

Analyze the provided transaction context and provide insights about:
- Likely merchant type
- Transaction patterns
- Risk factors
- Recommendations

Respond with a JSON object containing:
- "merchant_insights": insights about the merchant (object)
- "risk_assessment": risk level and factors (object)
- "recommendations": suggestions for routing optimization (array)
- "confidence": overall confidence in analysis (number)

Example: {"merchant_insights": {"type": "restaurant", "likely_chain": true}, "risk_assessment": {"level": "low", "factors": []}, "recommendations": ["use_dining_rewards_card"], "confidence": 0.8}"""
    
    def _create_mcc_prompt(self, context: Dict[str, Any]) -> str:
        """
        Create prompt for MCC prediction
        """
        prompt_parts = ["Predict the MCC for this transaction context:"]
        
        if context.get("time_of_day") is not None:
            hour = context["time_of_day"]
            if 6 <= hour <= 10:
                prompt_parts.append(f"- Time: {hour}:00 (morning, likely breakfast/coffee)")
            elif 11 <= hour <= 14:
                prompt_parts.append(f"- Time: {hour}:00 (lunch time)")
            elif 17 <= hour <= 21:
                prompt_parts.append(f"- Time: {hour}:00 (dinner time)")
            else:
                prompt_parts.append(f"- Time: {hour}:00")
        
        if context.get("day_of_week"):
            prompt_parts.append(f"- Day: {context['day_of_week']}")
        
        if context.get("pos_type"):
            prompt_parts.append(f"- POS System: {context['pos_type']}")
        
        if context.get("terminal_type"):
            prompt_parts.append(f"- Terminal Type: {context['terminal_type']}")
        
        if context.get("has_location"):
            prompt_parts.append("- Location data available")
        
        if context.get("wifi_count", 0) > 0:
            prompt_parts.append(f"- {context['wifi_count']} Wi-Fi networks detected")
        
        if context.get("ble_count", 0) > 0:
            prompt_parts.append(f"- {context['ble_count']} BLE devices detected")
        
        if context.get("amount"):
            amount = context["amount"]
            if amount < 10:
                prompt_parts.append(f"- Amount: ${amount:.2f} (small transaction)")
            elif amount > 100:
                prompt_parts.append(f"- Amount: ${amount:.2f} (large transaction)")
            else:
                prompt_parts.append(f"- Amount: ${amount:.2f}")
        
        prompt_parts.append("\nWhat is the most likely MCC? Provide your response as JSON.")
        
        return "\n".join(prompt_parts)
    
    def _create_merchant_prediction_prompt(self, merchant_name: str, context: Dict[str, Any] = None) -> str:
        """
        Create prompt for merchant category prediction
        """
        prompt_parts = [f"Analyze this merchant name and predict the MCC: '{merchant_name}'"]
        
        if context:
            if context.get("location_type"):
                prompt_parts.append(f"- Location type: {context['location_type']}")
            if context.get("time_of_day"):
                prompt_parts.append(f"- Transaction time: {context['time_of_day']}:00")
            if context.get("amount"):
                prompt_parts.append(f"- Transaction amount: ${context['amount']:.2f}")
        
        prompt_parts.append("\nProvide your analysis as JSON.")
        
        return "\n".join(prompt_parts)
    
    def _create_context_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """
        Create prompt for context analysis
        """
        prompt_parts = ["Analyze this transaction context:"]
        
        for key, value in context.items():
            if value is not None:
                prompt_parts.append(f"- {key}: {value}")
        
        prompt_parts.append("\nProvide detailed analysis as JSON.")
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response to extract MCC prediction
        """
        try:
            # Try to parse as JSON first
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                
                parsed = json.loads(json_str)
                
                # Validate required fields
                if "mcc" in parsed and len(str(parsed["mcc"])) == 4:
                    return {
                        "mcc": str(parsed["mcc"]),
                        "confidence": float(parsed.get("confidence", 0.3)),
                        "reasoning": parsed.get("reasoning", "LLM inference"),
                        "category": parsed.get("category", "unknown")
                    }
            
            # Fallback: extract MCC from text
            mcc_match = self._extract_mcc_from_text(response)
            if mcc_match:
                return {
                    "mcc": mcc_match,
                    "confidence": 0.3,
                    "reasoning": "Extracted from LLM text response",
                    "category": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        return None
    
    def _extract_mcc_from_text(self, text: str) -> Optional[str]:
        """
        Extract 4-digit MCC from text response
        """
        import re
        
        # Look for 4-digit numbers that could be MCCs
        mcc_pattern = r'\b(5\d{3}|4\d{3}|7\d{3}|6\d{3}|8\d{3}|9\d{3})\b'
        matches = re.findall(mcc_pattern, text)
        
        if matches:
            return matches[0]
        
        return None
    
    def _rule_based_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced rule-based MCC prediction when OpenAI is unavailable
        """
        hour = context.get("time_of_day", 12)
        day = context.get("day_of_week", "Monday")
        pos_type = context.get("pos_type", "").lower()
        amount = context.get("amount", 0)
        
        # Time-based rules with better logic
        if 6 <= hour <= 10:
            # Morning - likely coffee/breakfast
            if amount < 15:
                return {
                    "mcc": "5814",  # Fast food
                    "confidence": 0.5,
                    "reasoning": "Morning + small amount suggests coffee/breakfast",
                    "category": "fast_food"
                }
            else:
                return {
                    "mcc": "5812",  # Restaurant
                    "confidence": 0.4,
                    "reasoning": "Morning sit-down meal",
                    "category": "restaurant"
                }
        elif 11 <= hour <= 14:
            # Lunch time
            return {
                "mcc": "5812" if amount > 20 else "5814",
                "confidence": 0.5,
                "reasoning": f"Lunch time, ${amount:.2f} amount",
                "category": "restaurant" if amount > 20 else "fast_food"
            }
        elif 17 <= hour <= 21:
            # Dinner time
            return {
                "mcc": "5812",
                "confidence": 0.5,
                "reasoning": "Dinner time suggests restaurant",
                "category": "restaurant"
            }
        
        # POS type rules
        pos_patterns = {
            "toast": {"mcc": "5812", "confidence": 0.7, "category": "restaurant"},
            "restaurant": {"mcc": "5812", "confidence": 0.7, "category": "restaurant"},
            "square": {"mcc": "5999", "confidence": 0.4, "category": "retail"},
            "stripe": {"mcc": "5999", "confidence": 0.4, "category": "retail"},
            "clover": {"mcc": "5812", "confidence": 0.5, "category": "restaurant"}
        }
        
        for pattern, data in pos_patterns.items():
            if pattern in pos_type:
                return {
                    "mcc": data["mcc"],
                    "confidence": data["confidence"],
                    "reasoning": f"{pattern.title()} POS system detected",
                    "category": data["category"]
                }
        
        # Amount-based fallback
        if amount > 100:
            return {
                "mcc": "5311",  # Department store
                "confidence": 0.3,
                "reasoning": "Large amount suggests department store",
                "category": "retail"
            }
        elif amount < 5:
            return {
                "mcc": "5814",  # Fast food
                "confidence": 0.3,
                "reasoning": "Small amount suggests convenience purchase",
                "category": "convenience"
            }
        
        # Default fallback
        return {
            "mcc": "5999",  # Miscellaneous retail
            "confidence": 0.2,
            "reasoning": "Default miscellaneous retail fallback",
            "category": "retail"
        }


# Global instance
ai_inference_service = AIInferenceService() 