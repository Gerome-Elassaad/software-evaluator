import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from product_evaluator.config import settings
from product_evaluator.models.evaluation.criteria_model import Criterion
from product_evaluator.utils.logger import log_info, log_error, log_debug, log_execution_time


class TextAnalysisService:
    """Service for analyzing text using AI models."""
    
    def __init__(self):
        """Initialize the text analysis service."""
        # Configure the API key
        self._setup_api()
        
        # System prompt template for product analysis
        self.system_prompt_template = """
        You are an expert product evaluator specializing in software tools and services. 
        Your task is to analyze the provided text about a product and evaluate it based on specific criteria.
        
        Product information:
        {product_info}
        
        Evaluation criterion:
        {criterion_name}: {criterion_description}
        
        Your goal is to provide a thoughtful analysis of how well this product meets this specific criterion.
        Include specific observations, strengths, and weaknesses from the product information.
        Be balanced and objective in your assessment.
        Structure your response in 2-4 paragraphs.
        """
    
    def _setup_api(self):
        """Set up the AI API client."""
        try:
            # Configure Google Generative AI
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                log_info("Google Generative AI client configured")
            else:
                log_error("Google API key not found in environment")
        except Exception as e:
            log_error(f"Error setting up AI API client: {str(e)}")
    
    @log_execution_time
    async def analyze_product_for_criterion(
        self, 
        product_text: str, 
        criterion: Criterion,
        product_name: Optional[str] = None,
        product_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a product text for a specific evaluation criterion.
        
        Args:
            product_text: The extracted product text to analyze
            criterion: The evaluation criterion to assess
            product_name: Optional product name for context
            product_url: Optional product URL for reference
            
        Returns:
            Dictionary with analysis results
        """
        if not product_text or len(product_text) < 100:
            return {
                "error": "Insufficient product text for analysis",
                "analysis": "",
                "suggested_score": None,
            }
        
        try:
            # Create product info context
            product_info = f"Product name: {product_name}\n" if product_name else ""
            product_info += f"Product URL: {product_url}\n" if product_url else ""
            product_info += f"\nExtracted product information:\n{self._truncate_text(product_text, 6000)}"
            
            # Create the system prompt
            prompt = self.system_prompt_template.format(
                product_info=product_info,
                criterion_name=criterion.name,
                criterion_description=criterion.description
            )
            
            # If there's a custom prompt template for this criterion, use it
            if criterion.prompt_template:
                custom_prompt = criterion.prompt_template.format(
                    product_info=product_info,
                    product_name=product_name or "the product",
                    product_url=product_url or ""
                )
                prompt = custom_prompt
            
            # Run the inference
            response = await self._run_inference(prompt)
            
            if not response:
                return {
                    "error": "Failed to generate analysis",
                    "analysis": "",
                    "suggested_score": None,
                }
            
            # Follow up with a score suggestion
            score_prompt = f"""
            Based on your previous analysis of {product_name or 'the product'} 
            for the criterion "{criterion.name}", suggest a score from 1 to 10,
            where 1 is extremely poor and 10 is excellent.
            
            Return ONLY the numeric score without explanation.
            """
            
            score_response = await self._run_inference(score_prompt)
            suggested_score = None
            
            if score_response:
                # Extract just the number from the response
                import re
                score_match = re.search(r'\b([1-9]|10)\b', score_response)
                if score_match:
                    suggested_score = int(score_match.group(1))
            
            return {
                "error": None,
                "analysis": response,
                "suggested_score": suggested_score,
            }
            
        except Exception as e:
            log_error(f"Product analysis error: {str(e)}")
            return {
                "error": f"Analysis error: {str(e)}",
                "analysis": "",
                "suggested_score": None,
            }
    
    @log_execution_time
    async def analyze_product_for_multiple_criteria(
        self,
        product_text: str,
        criteria: List[Criterion],
        product_name: Optional[str] = None,
        product_url: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze a product text for multiple evaluation criteria.
        
        Args:
            product_text: The extracted product text to analyze
            criteria: List of evaluation criteria to assess
            product_name: Optional product name for context
            product_url: Optional product URL for reference
            
        Returns:
            Dictionary mapping criterion IDs to analysis results
        """
        if not product_text or len(product_text) < 100:
            return {
                criterion.id: {
                    "error": "Insufficient product text for analysis",
                    "analysis": "",
                    "suggested_score": None,
                }
                for criterion in criteria
            }
        
        # Create tasks for each criterion analysis
        tasks = [
            self.analyze_product_for_criterion(
                product_text, criterion, product_name, product_url
            )
            for criterion in criteria
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to criteria
        return {
            criterion.id: (
                results[i] if not isinstance(results[i], Exception) 
                else {
                    "error": f"Analysis error: {str(results[i])}",
                    "analysis": "",
                    "suggested_score": None,
                }
            )
            for i, criterion in enumerate(criteria)
        }
    
    async def _run_inference(self, prompt: str) -> str:
        """
        Run inference with the AI model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            Generated text response
        """
        try:
            # Use the configured AI model
            model = genai.GenerativeModel(
                model_name=settings.AI_MODEL_NAME,
                generation_config={
                    "temperature": settings.AI_TEMPERATURE,
                    "max_output_tokens": settings.AI_MAX_TOKENS,
                    "top_p": 0.9,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            )
            
            # Run the model in a thread to avoid blocking
            response = await asyncio.to_thread(
                model.generate_content, 
                prompt
            )
            
            # Check for valid response
            if response and response.parts:
                return response.text
            
            return ""
            
        except Exception as e:
            log_error(f"AI inference error: {str(e)}")
            return ""
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text to a maximum length.
        
        Args:
            text: The text to truncate
            max_length: Maximum length in characters
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Try to truncate at a paragraph break
        paragraphs = text.split("\n\n")
        result = ""
        
        for p in paragraphs:
            if len(result) + len(p) + 2 <= max_length:
                if result:
                    result += "\n\n"
                result += p
            else:
                remaining = max_length - len(result)
                if remaining > 100:  # Only add a partial paragraph if significant space remains
                    if result:
                        result += "\n\n"
                    result += p[:remaining - 5] + " [...]"
                break
        
        return result


# Singleton instance
analyzer = TextAnalysisService()


# Convenience functions for module-level usage
async def analyze_for_criterion(
    product_text: str, 
    criterion: Criterion,
    product_name: Optional[str] = None,
    product_url: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze product text for a specific criterion."""
    global analyzer
    return await analyzer.analyze_product_for_criterion(
        product_text, criterion, product_name, product_url
    )


async def analyze_for_multiple_criteria(
    product_text: str,
    criteria: List[Criterion],
    product_name: Optional[str] = None,
    product_url: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Analyze product text for multiple criteria."""
    global analyzer
    return await analyzer.analyze_product_for_multiple_criteria(
        product_text, criteria, product_name, product_url
    )