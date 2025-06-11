"""
Enhanced LLM Service for MCC Prediction
Uses OpenAI GPT models for intelligent merchant categorization and reasoning
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
import re
from datetime import datetime
import os

import openai
from openai import AsyncOpenAI

from ..core.config import settings
from ..database.supabase_client import get_supabase_client
from app.utils.mcc_categories import get_all_mcc_categories

logger = logging.getLogger(__name__)

class LLMService:
    """Enhanced LLM service for intelligent MCC prediction"""
    
    def __init__(self):
        self.client = None
        self.supabase = None
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        
        # MCC knowledge base - Use centralized utility
        self.mcc_categories = get_all_mcc_categories()
        
    async def initialize(self):
        """Initialize the LLM service"""
        try:
            api_key = settings.openai_api_key
            if not api_key:
                logger.warning("OpenAI API key not found - LLM service will be disabled")
                return
            
            self.client = AsyncOpenAI(api_key=api_key)
            
            # Test the connection
            await self._test_connection()
            
            # Initialize database (synchronous call, no await needed)
            self.supabase = get_supabase_client()
            
            # Create LLM analysis table if it doesn't exist
            if self.supabase.is_available:
                await self._create_llm_tables()
                logger.info("LLM service database connectivity verified")
            else:
                logger.warning("LLM service: Supabase not available, analysis storage disabled")
            
            logger.info("LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {str(e)}")
            self.client = None
    
    async def _test_connection(self):
        """Test OpenAI API connection"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            logger.info("OpenAI API connection successful")
        except Exception as e:
            logger.error(f"OpenAI API connection failed: {str(e)}")
            raise
    
    async def _create_llm_tables(self):
        """Create LLM analysis tables if they don't exist"""
        try:
            if not self.supabase:
                return
            
            # Create llm_analyses table for storing LLM predictions and learning
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS llm_analyses (
                    id BIGSERIAL PRIMARY KEY,
                    merchant_name TEXT,
                    llm_prediction TEXT,
                    llm_confidence DECIMAL(3,2),
                    llm_reasoning TEXT,
                    final_prediction TEXT,
                    final_confidence DECIMAL(3,2),
                    enhancement_applied BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                -- Create index for faster queries
                CREATE INDEX IF NOT EXISTS idx_llm_analyses_merchant 
                ON llm_analyses(merchant_name);
                
                CREATE INDEX IF NOT EXISTS idx_llm_analyses_created 
                ON llm_analyses(created_at);
                
                -- Create table for LLM model performance tracking
                CREATE TABLE IF NOT EXISTS llm_performance (
                    id BIGSERIAL PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    avg_confidence DECIMAL(3,2),
                    total_predictions INTEGER DEFAULT 0,
                    successful_predictions INTEGER DEFAULT 0,
                    failed_predictions INTEGER DEFAULT 0,
                    avg_response_time_ms INTEGER,
                    date_tracked DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(model_name, date_tracked)
                );
            """
            
            # Execute the SQL using Supabase
            response = await self.supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
            
            logger.info("LLM database tables created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create LLM tables: {str(e)}")
            # Continue without tables - service will work but won't store analyses
    
    async def enhance_mcc_prediction(self, 
                                   merchant_data: Dict[str, Any],
                                   existing_predictions: List[Dict[str, Any]],
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Use LLM to enhance MCC prediction with intelligent reasoning
        
        Args:
            merchant_data: Information about the merchant
            existing_predictions: Predictions from other services
            context: Additional context information
        
        Returns:
            Enhanced MCC prediction with LLM reasoning
        """
        try:
            if not self.client:
                return self._get_disabled_result()
            
            # Prepare merchant analysis prompt
            analysis_prompt = self._build_merchant_analysis_prompt(
                merchant_data, existing_predictions, context
            )
            
            # Get LLM analysis
            llm_response = await self._get_llm_analysis(analysis_prompt)
            
            # Parse and validate response
            parsed_result = self._parse_llm_response(llm_response)
            
            # Combine with existing predictions
            enhanced_result = self._combine_with_existing_predictions(
                parsed_result, existing_predictions
            )
            
            # Store LLM analysis for learning
            await self._store_llm_analysis(merchant_data, parsed_result, enhanced_result)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in LLM MCC enhancement: {str(e)}")
            return self._get_fallback_result(existing_predictions)
    
    async def analyze_merchant_name(self, merchant_name: str, 
                                  additional_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze merchant name using LLM for MCC prediction
        
        Args:
            merchant_name: Name of the merchant
            additional_info: Additional context information
        
        Returns:
            LLM analysis of merchant category
        """
        try:
            if not self.client or not merchant_name:
                return self._get_disabled_result()
            
            prompt = self._build_merchant_name_prompt(merchant_name, additional_info)
            response = await self._get_llm_analysis(prompt)
            result = self._parse_llm_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing merchant name: {str(e)}")
            return self._get_disabled_result()
    
    async def resolve_ambiguous_predictions(self, 
                                          conflicting_predictions: List[Dict[str, Any]],
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to resolve conflicting MCC predictions
        
        Args:
            conflicting_predictions: List of different MCC predictions
            context: Context information to help resolve conflicts
        
        Returns:
            LLM-resolved MCC prediction with reasoning
        """
        try:
            if not self.client or len(conflicting_predictions) < 2:
                return self._get_disabled_result()
            
            prompt = self._build_conflict_resolution_prompt(conflicting_predictions, context)
            response = await self._get_llm_analysis(prompt)
            result = self._parse_llm_response(response)
            
            # Add conflict resolution metadata
            result['conflict_resolution'] = True
            result['original_predictions'] = conflicting_predictions
            
            return result
            
        except Exception as e:
            logger.error(f"Error resolving prediction conflicts: {str(e)}")
            return self._get_fallback_result(conflicting_predictions)
    
    async def analyze_business_description(self, description: str, 
                                         venue_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze business description from APIs using LLM
        
        Args:
            description: Business description text
            venue_data: Additional venue information
        
        Returns:
            LLM analysis of business category
        """
        try:
            if not self.client or not description:
                return self._get_disabled_result()
            
            prompt = self._build_description_analysis_prompt(description, venue_data)
            response = await self._get_llm_analysis(prompt)
            result = self._parse_llm_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing business description: {str(e)}")
            return self._get_disabled_result()
    
    def _build_merchant_analysis_prompt(self, merchant_data: Dict[str, Any], 
                                      existing_predictions: List[Dict[str, Any]],
                                      context: Dict[str, Any]) -> str:
        """Build comprehensive merchant analysis prompt"""
        
        # Extract merchant information
        merchant_name = merchant_data.get('merchant_name', 'Unknown')
        business_description = merchant_data.get('business_description', '')
        location_info = merchant_data.get('location_info', {})
        venue_types = merchant_data.get('venue_types', [])
        
        # Build MCC options
        mcc_options = "\n".join([f"- {code}: {desc}" for code, desc in self.mcc_categories.items()])
        
        # Build existing predictions summary
        predictions_summary = ""
        if existing_predictions:
            predictions_summary = "Existing Predictions:\n"
            for i, pred in enumerate(existing_predictions, 1):
                predictions_summary += f"{i}. {pred.get('method', 'Unknown')}: MCC {pred.get('mcc', 'Unknown')} (confidence: {pred.get('confidence', 0):.2f})\n"
        
        # Build context information
        context_info = ""
        if context:
            context_info = f"Additional Context:\n"
            for key, value in context.items():
                context_info += f"- {key}: {value}\n"
        
        prompt = f"""
You are an expert in merchant categorization and MCC (Merchant Category Code) classification. 
Analyze the following merchant information and provide the most accurate MCC prediction.

MERCHANT INFORMATION:
- Name: {merchant_name}
- Business Description: {business_description}
- Location: {location_info}
- Venue Types: {venue_types}

{predictions_summary}

{context_info}

AVAILABLE MCC CODES:
{mcc_options}

TASK:
1. Analyze all available information about this merchant
2. Consider the existing predictions and their confidence levels
3. Determine the most appropriate MCC code
4. Provide confidence level (0.0 to 1.0)
5. Explain your reasoning
6. Suggest alternative MCCs if uncertain

RESPONSE FORMAT (JSON):
{{
    "predicted_mcc": "XXXX",
    "confidence": 0.XX,
    "reasoning": "Detailed explanation of why this MCC was chosen",
    "alternative_mccs": [
        {{"mcc": "XXXX", "confidence": 0.XX, "reason": "explanation"}},
        {{"mcc": "XXXX", "confidence": 0.XX, "reason": "explanation"}}
    ],
    "key_factors": ["factor1", "factor2", "factor3"],
    "certainty_level": "high|medium|low"
}}

Focus on accuracy and provide clear reasoning for your decision.
"""
        
        return prompt
    
    def _build_merchant_name_prompt(self, merchant_name: str, 
                                  additional_info: Dict[str, Any]) -> str:
        """Build merchant name analysis prompt"""
        
        mcc_options = "\n".join([f"- {code}: {desc}" for code, desc in self.mcc_categories.items()])
        
        additional_context = ""
        if additional_info:
            additional_context = "Additional Information:\n"
            for key, value in additional_info.items():
                additional_context += f"- {key}: {value}\n"
        
        prompt = f"""
Analyze this merchant name and predict the most likely business category and MCC code.

MERCHANT NAME: "{merchant_name}"

{additional_context}

AVAILABLE MCC CODES:
{mcc_options}

Consider:
- Business type indicators in the name
- Common naming patterns for different industries
- Regional or cultural naming conventions
- Abbreviations or acronyms that might indicate business type

RESPONSE FORMAT (JSON):
{{
    "predicted_mcc": "XXXX",
    "confidence": 0.XX,
    "reasoning": "Why this MCC was chosen based on the name",
    "business_type_indicators": ["indicator1", "indicator2"],
    "name_analysis": "Analysis of the merchant name components",
    "alternative_mccs": [
        {{"mcc": "XXXX", "confidence": 0.XX, "reason": "explanation"}}
    ]
}}
"""
        
        return prompt
    
    def _build_conflict_resolution_prompt(self, conflicting_predictions: List[Dict[str, Any]], 
                                        context: Dict[str, Any]) -> str:
        """Build conflict resolution prompt"""
        
        # Format conflicting predictions
        conflicts = "CONFLICTING PREDICTIONS:\n"
        for i, pred in enumerate(conflicting_predictions, 1):
            method = pred.get('method', 'Unknown Method')
            mcc = pred.get('mcc', 'Unknown')
            confidence = pred.get('confidence', 0)
            source = pred.get('source', 'Unknown Source')
            
            conflicts += f"{i}. {method} ({source}): MCC {mcc} (confidence: {confidence:.2f})\n"
            if 'details' in pred:
                conflicts += f"   Details: {pred['details']}\n"
        
        # Format context
        context_info = ""
        if context:
            context_info = "ADDITIONAL CONTEXT:\n"
            for key, value in context.items():
                context_info += f"- {key}: {value}\n"
        
        mcc_options = "\n".join([f"- {code}: {desc}" for code, desc in self.mcc_categories.items()])
        
        prompt = f"""
You have multiple conflicting MCC predictions for the same merchant. 
Analyze each prediction and determine the most accurate MCC code.

{conflicts}

{context_info}

AVAILABLE MCC CODES:
{mcc_options}

ANALYSIS TASKS:
1. Evaluate the reliability of each prediction method
2. Consider the confidence levels and supporting evidence
3. Look for patterns or consensus among predictions
4. Identify which prediction has the strongest supporting evidence
5. Determine if any predictions should be discarded due to low quality

RESPONSE FORMAT (JSON):
{{
    "resolved_mcc": "XXXX",
    "confidence": 0.XX,
    "resolution_reasoning": "Detailed explanation of how the conflict was resolved",
    "method_analysis": {{
        "most_reliable": "method_name",
        "least_reliable": "method_name",
        "consensus_level": "high|medium|low"
    }},
    "supporting_evidence": ["evidence1", "evidence2"],
    "rejected_predictions": [
        {{"mcc": "XXXX", "method": "method_name", "reason_for_rejection": "explanation"}}
    ]
}}

Be thorough in your analysis and provide clear reasoning for your decision.
"""
        
        return prompt
    
    def _build_description_analysis_prompt(self, description: str, 
                                         venue_data: Dict[str, Any]) -> str:
        """Build business description analysis prompt"""
        
        venue_context = ""
        if venue_data:
            venue_context = "VENUE DATA:\n"
            for key, value in venue_data.items():
                venue_context += f"- {key}: {value}\n"
        
        mcc_options = "\n".join([f"- {code}: {desc}" for code, desc in self.mcc_categories.items()])
        
        prompt = f"""
Analyze this business description and determine the most appropriate MCC category.

BUSINESS DESCRIPTION:
"{description}"

{venue_context}

AVAILABLE MCC CODES:
{mcc_options}

ANALYSIS FOCUS:
- Key business activities mentioned
- Products or services offered
- Industry indicators and terminology
- Business model clues
- Target customer types

RESPONSE FORMAT (JSON):
{{
    "predicted_mcc": "XXXX",
    "confidence": 0.XX,
    "reasoning": "Analysis of the description and why this MCC fits",
    "key_terms": ["term1", "term2", "term3"],
    "business_activities": ["activity1", "activity2"],
    "industry_indicators": ["indicator1", "indicator2"],
    "alternative_mccs": [
        {{"mcc": "XXXX", "confidence": 0.XX, "reason": "explanation"}}
    ]
}}
"""
        
        return prompt
    
    async def _get_llm_analysis(self, prompt: str) -> str:
        """Get analysis from LLM"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert in merchant categorization and MCC classification. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting LLM analysis: {str(e)}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Parse JSON response
            parsed = json.loads(response)
            
            # Validate required fields
            required_fields = ['predicted_mcc', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate MCC format
            mcc = parsed['predicted_mcc']
            if not re.match(r'^\d{4}$', str(mcc)):
                raise ValueError(f"Invalid MCC format: {mcc}")
            
            # Validate confidence range
            confidence = float(parsed['confidence'])
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"Confidence out of range: {confidence}")
            
            # Add metadata
            parsed['method'] = 'llm_analysis'
            parsed['source'] = 'openai_gpt'
            parsed['timestamp'] = datetime.now().isoformat()
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM: {e}")
            raise ValueError("LLM returned invalid JSON")
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            raise
    
    def _combine_with_existing_predictions(self, llm_result: Dict[str, Any], 
                                         existing_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine LLM analysis with existing predictions"""
        
        # Add LLM prediction to the list
        all_predictions = existing_predictions + [llm_result]
        
        # Calculate weighted consensus
        mcc_scores = {}
        total_weight = 0
        
        # Weight LLM prediction higher for reasoning capability
        llm_weight = 0.4
        other_weight = 0.6 / len(existing_predictions) if existing_predictions else 0.6
        
        # Score LLM prediction
        llm_mcc = llm_result['predicted_mcc']
        llm_confidence = llm_result['confidence']
        mcc_scores[llm_mcc] = mcc_scores.get(llm_mcc, 0) + (llm_confidence * llm_weight)
        total_weight += llm_weight
        
        # Score existing predictions
        for pred in existing_predictions:
            mcc = pred.get('mcc', '5999')
            confidence = pred.get('confidence', 0.5)
            mcc_scores[mcc] = mcc_scores.get(mcc, 0) + (confidence * other_weight)
            total_weight += other_weight
        
        # Find best MCC
        if mcc_scores:
            best_mcc = max(mcc_scores, key=mcc_scores.get)
            best_score = mcc_scores[best_mcc] / total_weight if total_weight > 0 else 0
        else:
            best_mcc = llm_mcc
            best_score = llm_confidence
        
        return {
            'predicted_mcc': best_mcc,
            'confidence': min(0.95, best_score),  # Cap at 95%
            'method': 'llm_enhanced_consensus',
            'source': 'hybrid_analysis',
            'llm_analysis': llm_result,
            'all_predictions': all_predictions,
            'consensus_score': best_score,
            'enhancement_applied': True
        }
    
    async def _store_llm_analysis(self, merchant_data: Dict[str, Any], 
                                llm_result: Dict[str, Any], 
                                final_result: Dict[str, Any]):
        """Store LLM analysis for future learning"""
        try:
            if not self.supabase:
                return
            
            analysis_record = {
                'merchant_name': merchant_data.get('merchant_name', ''),
                'llm_prediction': llm_result['predicted_mcc'],
                'llm_confidence': llm_result['confidence'],
                'llm_reasoning': llm_result['reasoning'],
                'final_prediction': final_result['predicted_mcc'],
                'final_confidence': final_result['confidence'],
                'enhancement_applied': final_result.get('enhancement_applied', False),
                'created_at': datetime.now().isoformat()
            }
            
            await self.supabase.table('llm_analyses').insert(analysis_record).execute()
            
        except Exception as e:
            logger.error(f"Error storing LLM analysis: {str(e)}")
    
    def _get_disabled_result(self) -> Dict[str, Any]:
        """Return result when LLM service is disabled"""
        return {
            'predicted_mcc': None,
            'confidence': 0.0,
            'method': 'llm_disabled',
            'source': 'service_unavailable',
            'enhancement_applied': False,
            'error': 'LLM service not available'
        }
    
    def _get_fallback_result(self, existing_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return fallback result when LLM fails"""
        if existing_predictions:
            # Use best existing prediction
            best_pred = max(existing_predictions, key=lambda x: x.get('confidence', 0))
            return {
                'predicted_mcc': best_pred.get('mcc', '5999'),
                'confidence': best_pred.get('confidence', 0.5),
                'method': 'llm_fallback',
                'source': 'existing_prediction',
                'enhancement_applied': False,
                'fallback_used': True
            }
        else:
            return {
                'predicted_mcc': '5999',
                'confidence': 0.3,
                'method': 'llm_fallback',
                'source': 'default',
                'enhancement_applied': False,
                'fallback_used': True
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get LLM service status and capabilities"""
        return {
            'service_available': self.client is not None,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'capabilities': [
                'merchant_name_analysis',
                'business_description_analysis', 
                'conflict_resolution',
                'comprehensive_enhancement'
            ],
            'mcc_categories_count': len(self.mcc_categories)
        } 