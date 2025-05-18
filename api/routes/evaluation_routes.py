from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from sqlalchemy import desc

from product_evaluator.models.user.user_model import User
from product_evaluator.models.product.product_model import Product
from product_evaluator.models.evaluation.evaluation_model import Evaluation
from product_evaluator.models.evaluation.criteria_model import Criterion, CriterionEvaluation
from product_evaluator.services.auth.authentication import get_current_active_user
from product_evaluator.services.ai.text_analysis import analyze_for_multiple_criteria
from product_evaluator.services.ai.summary_generation import generate_summary
from product_evaluator.utils.database import get_db
from product_evaluator.utils.logger import log_info, log_error, log_execution_time


router = APIRouter(tags=["evaluations"])


# --- Pydantic Models ---

class CriterionEvaluationInput(BaseModel):
    """Schema for criterion evaluation input."""
    criterion_id: str
    score: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class EvaluationCreate(BaseModel):
    """Schema for creating a new evaluation."""
    title: str = Field(..., min_length=1, max_length=100)
    product_id: str
    criteria_evaluations: List[CriterionEvaluationInput] = []
    notes: Optional[str] = None
    use_ai_analysis: bool = False
    
    @validator('criteria_evaluations')
    def validate_unique_criteria(cls, v):
        """Validate that each criterion is only evaluated once."""
        criterion_ids = [ce.criterion_id for ce in v]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("Each criterion can only be evaluated once")
        return v


class EvaluationUpdate(BaseModel):
    """Schema for updating an evaluation."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    criteria_evaluations: Optional[List[CriterionEvaluationInput]] = None
    notes: Optional[str] = None
    is_published: Optional[bool] = None
    generate_ai_summary: bool = False
    
    @validator('criteria_evaluations')
    def validate_unique_criteria(cls, v):
        """Validate that each criterion is only evaluated once."""
        if v is None:
            return v
        criterion_ids = [ce.criterion_id for ce in v]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("Each criterion can only be evaluated once")
        return v


class CriterionEvaluationResponse(BaseModel):
    """Schema for criterion evaluation in responses."""
    id: str
    criterion_id: str
    criterion_name: str
    criterion_description: Optional[str] = None
    criterion_category: Optional[str] = None
    criterion_weight: int
    score: Optional[int] = None
    notes: Optional[str] = None
    ai_generated_assessment: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Schema for evaluation data in responses."""
    id: str
    title: str
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    is_published: bool
    created_at: str
    updated_at: str
    user_id: str
    product_id: str
    product_name: str
    product_description: Optional[str] = None
    ai_generated_summary: Optional[str] = None
    criteria_evaluations: List[CriterionEvaluationResponse] = []
    
    class Config:
        from_attributes = True


class AIAnalysisRequest(BaseModel):
    """Schema for requesting AI analysis of a product."""
    product_id: str
    criteria_ids: List[str] = []


class AIAnalysisResponse(BaseModel):
    """Schema for AI analysis response."""
    product_id: str
    criteria_analyses: Dict[str, Dict[str, Any]]
    error: Optional[str] = None


class AISummaryRequest(BaseModel):
    """Schema for requesting AI summary generation."""
    evaluation_id: str
    include_recommendations: bool = True


class AISummaryResponse(BaseModel):
    """Schema for AI summary response."""
    evaluation_id: str
    summary: str
    error: Optional[str] = None


# --- Helper Functions ---

def get_criterion_by_id(criterion_id: str, db: Session) -> Optional[Criterion]:
    """Get a criterion by ID."""
    return db.query(Criterion).filter(Criterion.id == criterion_id).first()


async def perform_ai_analysis_for_evaluation(
    evaluation_id: str,
    db: Session
) -> None:
    """
    Background task to perform AI analysis for an evaluation.
    
    Args:
        evaluation_id: ID of the evaluation
        db: Database session
    """
    try:
        # Get the evaluation
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation or not evaluation.product:
            log_error(f"Evaluation or product not found for AI analysis: {evaluation_id}")
            return
        
        # Check if product has extracted content
        product = evaluation.product
        if not product.extracted_content or len(product.extracted_content) < 100:
            log_error(f"Insufficient extracted content for product: {product.id}")
            return
        
        # Get criteria from the evaluation
        criteria_ids = [ce.criterion_id for ce in evaluation.criterion_evaluations]
        criteria = db.query(Criterion).filter(Criterion.id.in_(criteria_ids)).all()
        
        if not criteria:
            log_error(f"No criteria found for evaluation: {evaluation_id}")
            return
        
        # Perform AI analysis
        analysis_results = await analyze_for_multiple_criteria(
            product.extracted_content,
            criteria,
            product.name,
            product.website_url
        )
        
        # Update criterion evaluations with AI analysis
        for ce in evaluation.criterion_evaluations:
            if ce.criterion_id in analysis_results:
                result = analysis_results[ce.criterion_id]
                ce.ai_generated_assessment = result.get("analysis", "")
                
                # Set suggested score if no user score is set
                if ce.score is None and result.get("suggested_score") is not None:
                    ce.score = result["suggested_score"]
        
        # Update overall score
        evaluation.update_overall_score()
        
        # Generate AI summary
        if evaluation.overall_score is not None:
            summary_result = await generate_summary(evaluation)
            if not summary_result.get("error"):
                evaluation.ai_generated_summary = summary_result.get("summary", "")
                
                # If no user summary, use AI summary
                if not evaluation.summary:
                    evaluation.summary = evaluation.ai_generated_summary
        
        # Update database
        db.commit()
        log_info(f"AI analysis completed for evaluation: {evaluation_id}")
        
    except Exception as e:
        db.rollback()
        log_error(f"Error during AI analysis for evaluation {evaluation_id}: {str(e)}")


# --- Routes ---

@router.post("/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new evaluation."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == evaluation_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Create evaluation
    evaluation = Evaluation(
        title=evaluation_data.title,
        notes=evaluation_data.notes,
        user_id=current_user.id,
        product_id=evaluation_data.product_id,
    )
    
    # Add to database first to get ID
    db.add(evaluation)
    db.flush()
    
    # Add criterion evaluations
    for ce_data in evaluation_data.criteria_evaluations:
        criterion = get_criterion_by_id(ce_data.criterion_id, db)
        if not criterion:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Criterion not found: {ce_data.criterion_id}"
            )
        
        criterion_evaluation = CriterionEvaluation(
            criterion_id=ce_data.criterion_id,
            evaluation_id=evaluation.id,
            score=ce_data.score,
            notes=ce_data.notes,
        )
        
        db.add(criterion_evaluation)
    
    # Calculate overall score
    db.flush()
    evaluation.update_overall_score()
    
    # Commit to database
    db.commit()
    db.refresh(evaluation)
    
    log_info(f"Evaluation created: {evaluation.title} by user {current_user.username}")
    
    # If AI analysis is requested, do it in the background
    if evaluation_data.use_ai_analysis and product.extracted_content:
        background_tasks.add_task(
            perform_ai_analysis_for_evaluation,
            evaluation.id,
            SessionLocal()
        )
        log_info(f"AI analysis scheduled for evaluation: {evaluation.id}")
    
    # Prepare response data
    response_data = prepare_evaluation_response(evaluation, db)
    return response_data


@router.get("/evaluations", response_model=List[EvaluationResponse])
async def get_evaluations(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[str] = None,
    user_id: Optional[str] = None,
    published_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all evaluations with optional filtering."""
    query = db.query(Evaluation)
    
    # Apply filters
    if product_id:
        query = query.filter(Evaluation.product_id == product_id)
    
    if user_id:
        # If requesting other user's evaluations, only show published ones
        if user_id != current_user.id and not current_user.is_admin:
            query = query.filter(Evaluation.user_id == user_id, Evaluation.is_published == True)
        else:
            query = query.filter(Evaluation.user_id == user_id)
    elif not current_user.is_admin:
        # Regular users can see their own evaluations and published evaluations from others
        query = query.filter(
            (Evaluation.user_id == current_user.id) | (Evaluation.is_published == True)
        )
    
    if published_only:
        query = query.filter(Evaluation.is_published == True)
    
    # Apply sorting and pagination
    query = query.order_by(desc(Evaluation.created_at))
    evaluations = query.offset(skip).limit(limit).all()
    
    # Prepare response data
    return [prepare_evaluation_response(evaluation, db) for evaluation in evaluations]


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get an evaluation by ID."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check permissions - users can only see their own evaluations or published ones
    if (evaluation.user_id != current_user.id and not evaluation.is_published 
            and not current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: this evaluation is not published"
        )
    
    # Prepare response data
    response_data = prepare_evaluation_response(evaluation, db)
    return response_data


@router.put("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
async def update_evaluation(
    evaluation_id: str,
    evaluation_data: EvaluationUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check if user is the creator or an admin
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can update this evaluation"
        )
    
    # Update fields if provided
    if evaluation_data.title is not None:
        evaluation.title = evaluation_data.title
    
    if evaluation_data.notes is not None:
        evaluation.notes = evaluation_data.notes
    
    if evaluation_data.is_published is not None:
        evaluation.is_published = evaluation_data.is_published
    
    # Update criteria evaluations if provided
    if evaluation_data.criteria_evaluations is not None:
        # Get existing criterion evaluations
        existing_ces = {ce.criterion_id: ce for ce in evaluation.criterion_evaluations}
        
        for ce_data in evaluation_data.criteria_evaluations:
            if ce_data.criterion_id in existing_ces:
                # Update existing criterion evaluation
                ce = existing_ces[ce_data.criterion_id]
                if ce_data.score is not None:
                    ce.score = ce_data.score
                if ce_data.notes is not None:
                    ce.notes = ce_data.notes
            else:
                # Create new criterion evaluation
                criterion = get_criterion_by_id(ce_data.criterion_id, db)
                if not criterion:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Criterion not found: {ce_data.criterion_id}"
                    )
                
                ce = CriterionEvaluation(
                    criterion_id=ce_data.criterion_id,
                    evaluation_id=evaluation.id,
                    score=ce_data.score,
                    notes=ce_data.notes,
                )
                
                db.add(ce)
    
    # Update overall score
    db.flush()
    evaluation.update_overall_score()
    
    # Generate AI summary if requested
    if evaluation_data.generate_ai_summary:
        background_tasks.add_task(
            generate_ai_summary_for_evaluation,
            evaluation.id,
            SessionLocal()
        )
        log_info(f"AI summary generation scheduled for evaluation: {evaluation.id}")
    
    # Commit to database
    db.commit()
    db.refresh(evaluation)
    
    log_info(f"Evaluation updated: {evaluation.title} by user {current_user.username}")
    
    # Prepare response data
    response_data = prepare_evaluation_response(evaluation, db)
    return response_data


@router.delete("/evaluations/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check if user is the creator or an admin
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can delete this evaluation"
        )
    
    # Delete the evaluation
    db.delete(evaluation)
    db.commit()
    
    log_info(f"Evaluation deleted: {evaluation.title} by user {current_user.username}")
    
    return None


@router.post("/evaluations/{evaluation_id}/publish", response_model=EvaluationResponse)
async def publish_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Publish an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check if user is the creator or an admin
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can publish this evaluation"
        )
    
    # Publish the evaluation
    evaluation.is_published = True
    db.commit()
    db.refresh(evaluation)
    
    log_info(f"Evaluation published: {evaluation.title} by user {current_user.username}")
    
    # Prepare response data
    response_data = prepare_evaluation_response(evaluation, db)
    return response_data


@router.post("/evaluations/{evaluation_id}/unpublish", response_model=EvaluationResponse)
async def unpublish_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unpublish an evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check if user is the creator or an admin
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can unpublish this evaluation"
        )
    
    # Unpublish the evaluation
    evaluation.is_published = False
    db.commit()
    db.refresh(evaluation)
    
    log_info(f"Evaluation unpublished: {evaluation.title} by user {current_user.username}")
    
    # Prepare response data
    response_data = prepare_evaluation_response(evaluation, db)
    return response_data


@router.post("/ai/analyze", response_model=AIAnalysisResponse)
@log_execution_time
async def analyze_product(
    analysis_request: AIAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze a product with AI for specific criteria."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == analysis_request.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if product has extracted content
    if not product.extracted_content or len(product.extracted_content) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient extracted content for product"
        )
    
    # Get criteria
    if analysis_request.criteria_ids:
        criteria = db.query(Criterion).filter(Criterion.id.in_(analysis_request.criteria_ids)).all()
    else:
        # Use default criteria if none specified
        criteria = db.query(Criterion).filter(Criterion.is_default == True).all()
    
    if not criteria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No criteria found for analysis"
        )
    
    try:
        # Perform AI analysis
        analysis_results = await analyze_for_multiple_criteria(
            product.extracted_content,
            criteria,
            product.name,
            product.website_url
        )
        
        return {
            "product_id": product.id,
            "criteria_analyses": analysis_results,
            "error": None
        }
    except Exception as e:
        log_error(f"AI analysis error: {str(e)}")
        return {
            "product_id": product.id,
            "criteria_analyses": {},
            "error": str(e)
        }


@router.post("/ai/summarize", response_model=AISummaryResponse)
@log_execution_time
async def summarize_evaluation(
    summary_request: AISummaryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate an AI summary for an evaluation."""
    # Check if evaluation exists
    evaluation = db.query(Evaluation).filter(Evaluation.id == summary_request.evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )
    
    # Check if user is the creator or an admin
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only the creator or an admin can generate summaries"
        )
    
    try:
        # Generate summary
        summary_result = await generate_summary(evaluation, summary_request.include_recommendations)
        
        if summary_result.get("error"):
            return {
                "evaluation_id": evaluation.id,
                "summary": "",
                "error": summary_result["error"]
            }
        
        # Update evaluation with generated summary
        evaluation.ai_generated_summary = summary_result["summary"]
        db.commit()
        
        return {
            "evaluation_id": evaluation.id,
            "summary": summary_result["summary"],
            "error": None
        }
    except Exception as e:
        log_error(f"AI summary generation error: {str(e)}")
        return {
            "evaluation_id": evaluation.id,
            "summary": "",
            "error": str(e)
        }


@router.get("/criteria", response_model=List[Criterion])
async def get_criteria(
    category: Optional[str] = None,
    is_default: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all evaluation criteria with optional filtering."""
    query = db.query(Criterion)
    
    # Apply filters
    if category:
        query = query.filter(Criterion.category == category)
    
    if is_default is not None:
        query = query.filter(Criterion.is_default == is_default)
    
    criteria = query.all()
    return criteria


@router.get("/criteria/categories", response_model=List[str])
async def get_criterion_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a list of all criterion categories."""
    categories = db.query(Criterion.category).distinct().filter(Criterion.category.isnot(None)).all()
    return [category[0] for category in categories]


@router.get("/criteria/{criterion_id}", response_model=Criterion)
async def get_criterion(
    criterion_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a criterion by ID."""
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    
    if not criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Criterion not found"
        )
    
    return criterion


# --- Utility Functions ---

def prepare_evaluation_response(evaluation: Evaluation, db: Session) -> Dict[str, Any]:
    """
    Prepare evaluation data for response.
    
    Args:
        evaluation: Evaluation object
        db: Database session
        
    Returns:
        Dictionary with evaluation data
    """
    # Get criterion evaluations with additional data
    criteria_evaluations = []
    
    for ce in evaluation.criterion_evaluations:
        criterion = ce.criterion
        
        if criterion:
            criteria_evaluations.append({
                "id": ce.id,
                "criterion_id": criterion.id,
                "criterion_name": criterion.name,
                "criterion_description": criterion.description,
                "criterion_category": criterion.category,
                "criterion_weight": criterion.weight,
                "score": ce.score,
                "notes": ce.notes,
                "ai_generated_assessment": ce.ai_generated_assessment,
            })
    
    # Get product data
    product_name = "Unknown"
    product_description = None
    
    if evaluation.product:
        product_name = evaluation.product.name
        product_description = evaluation.product.description
    
    # Prepare response data
    return {
        "id": evaluation.id,
        "title": evaluation.title,
        "overall_score": evaluation.overall_score,
        "summary": evaluation.summary,
        "notes": evaluation.notes,
        "is_published": evaluation.is_published,
        "created_at": evaluation.created_at.isoformat(),
        "updated_at": evaluation.updated_at.isoformat(),
        "user_id": evaluation.user_id,
        "product_id": evaluation.product_id,
        "product_name": product_name,
        "product_description": product_description,
        "ai_generated_summary": evaluation.ai_generated_summary,
        "criteria_evaluations": criteria_evaluations,
    }


async def generate_ai_summary_for_evaluation(evaluation_id: str, db: Session) -> None:
    """
    Background task to generate AI summary for an evaluation.
    
    Args:
        evaluation_id: ID of the evaluation
        db: Database session
    """
    try:
        # Get the evaluation
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            log_error(f"Evaluation not found for AI summary generation: {evaluation_id}")
            return
        
        # Generate summary
        summary_result = await generate_summary(evaluation)
        
        if not summary_result.get("error"):
            evaluation.ai_generated_summary = summary_result.get("summary", "")
            
            # If no user summary, use AI summary
            if not evaluation.summary:
                evaluation.summary = evaluation.ai_generated_summary
            
            # Update database
            db.commit()
            log_info(f"AI summary generated for evaluation: {evaluation_id}")
        else:
            log_error(f"Error generating AI summary: {summary_result.get('error')}")
        
    except Exception as e:
        db.rollback()
        log_error(f"Error during AI summary generation for evaluation {evaluation_id}: {str(e)}")


# Import the SessionLocal class for background tasks
from product_evaluator.utils.database import SessionLocal