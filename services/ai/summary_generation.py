import asyncio
from typing import Dict, List, Optional, Any

import google.generativeai as genai

from product_evaluator.config import settings
from product_evaluator.models.evaluation.criteria_model import Criterion, CriterionEvaluation
from product_evaluator.models.evaluation.evaluation_model import Evaluation
from product_evaluator.utils.logger import log_info, log_error, log_debug, log_execution_time


class SummaryGenerator:
    """Service for generating summaries of product evaluations using AI."""
    
    def __init__(self):
        """Initialize the summary generator service."""
        # Configure the API key
        self._setup_api()
        
        # System prompt template for summary generation
        self.summary_prompt_template = """
        You are an expert product evaluator summarizing the results of a detailed product evaluation.
        
        Product: {product_name}
        Overall Score: {overall_score}/10
        
        Criteria Evaluations:
        {criteria_evaluations}
        
        Your task is to create a comprehensive summary of this evaluation. The summary should:
        1. Start with a clear overall assessment of the product's strengths and weaknesses
        2. Highlight the most important findings from each criterion
        3. Include specific examples or evidence from the evaluation where relevant
        4. End with a clear conclusion about who would benefit most from this product
        
        Create a structured, balanced summary of approximately 300-500 words.
        Use headers to organize the content.
        """
    
    def _setup_api(self):
        """Set up the AI API client."""
        try:
            # Configure Google Generative AI
            if settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                log_info("Google Generative AI client configured for summary generation")
            else:
                log_error("Google API key not found in environment")
        except Exception as e:
            log_error(f"Error setting up AI API client for summary generation: {str(e)}")
    
    @log_execution_time
    async def generate_evaluation_summary(
        self, 
        evaluation: Evaluation,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a summary for a product evaluation.
        
        Args:
            evaluation: The evaluation object with criteria evaluations
            include_recommendations: Whether to include recommendations in the summary
            
        Returns:
            Dictionary with the generated summary
        """
        if not evaluation or not evaluation.criterion_evaluations:
            return {
                "error": "Insufficient evaluation data for summary generation",
                "summary": "",
            }
        
        try:
            # Format criteria evaluations for the prompt
            criteria_text = self._format_criteria_evaluations(evaluation.criterion_evaluations)
            
            # Get product name
            product_name = evaluation.product.name if evaluation.product else "Product"
            
            # Create the prompt
            prompt = self.summary_prompt_template.format(
                product_name=product_name,
                overall_score=evaluation.overall_score or "N/A",
                criteria_evaluations=criteria_text
            )
            
            # Add recommendation request if needed
            if include_recommendations:
                prompt += "\nAlso include a section called 'Recommendations' with 2-3 concrete suggestions for how this product could be improved."
            
            # Run the inference
            summary = await self._run_inference(prompt)
            
            if not summary:
                return {
                    "error": "Failed to generate summary",
                    "summary": "",
                }
            
            return {
                "error": None,
                "summary": summary,
            }
            
        except Exception as e:
            log_error(f"Summary generation error: {str(e)}")
            return {
                "error": f"Summary generation error: {str(e)}",
                "summary": "",
            }
    
    def _format_criteria_evaluations(self, criterion_evaluations: List[CriterionEvaluation]) -> str:
        """
        Format criterion evaluations for the summary prompt.
        
        Args:
            criterion_evaluations: List of criterion evaluations
            
        Returns:
            Formatted text of criterion evaluations
        """
        formatted_text = ""
        
        for i, ce in enumerate(criterion_evaluations):
            criterion_name = ce.criterion.name if ce.criterion else f"Criterion {i+1}"
            score = f"{ce.score}/10" if ce.score is not None else "N/A"
            
            formatted_text += f"## {criterion_name}: {score}\n"
            
            # Add AI-generated assessment if available
            if ce.ai_generated_assessment:
                assessment = ce.ai_generated_assessment.strip()
                # Truncate if too long
                if len(assessment) > 500:
                    assessment = assessment[:497] + "..."
                formatted_text += f"{assessment}\n\n"
            
            # Add user notes if available
            if ce.notes:
                formatted_text += f"User notes: {ce.notes}\n\n"
            
            if not ce.ai_generated_assessment and not ce.notes:
                formatted_text += "No detailed assessment available.\n\n"
        
        return formatted_text
    
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
                    "temperature": 0.4,  # Lower temperature for more consistent summaries
                    "max_output_tokens": 2048,
                    "top_p": 0.95,
                },
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
            log_error(f"AI inference error during summary generation: {str(e)}")
            return ""


# Singleton instance
summary_generator = SummaryGenerator()


# Convenience function for module-level usage
async def generate_summary(
    evaluation: Evaluation,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """Generate a summary for an evaluation."""
    global summary_generator
    return await summary_generator.generate_evaluation_summary(
        evaluation, include_recommendations
    )