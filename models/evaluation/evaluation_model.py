import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from product_evaluator.utils.database import Base


class Evaluation(Base):
    """Model for product evaluations conducted by users."""
    
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(100), nullable=False)
    overall_score = Column(Float, nullable=True)  # Overall score from 1-10
    summary = Column(Text, nullable=True)  # User's summary or AI-generated summary
    notes = Column(Text, nullable=True)  # Additional notes by the user
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    
    # AI-generated content
    ai_generated_summary = Column(Text, nullable=True)
    ai_generated_scores = Column(JSON, nullable=True)  # JSON formatted AI-suggested scores
    
    # Relationships
    user = relationship("User", back_populates="evaluations")
    product = relationship("Product", back_populates="evaluations")
    criteria = relationship(
        "Criterion", 
        secondary="criterion_evaluations", 
        back_populates="evaluations"
    )
    criterion_evaluations = relationship(
        "CriterionEvaluation", 
        back_populates="evaluation", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Evaluation {self.title}>"
    
    def calculate_overall_score(self) -> float:
        """Calculate weighted average score across all criteria."""
        if not self.criterion_evaluations:
            return 0.0
        
        total_weight = 0
        weighted_sum = 0
        
        for criterion_eval in self.criterion_evaluations:
            if criterion_eval.score is not None and criterion_eval.criterion is not None:
                weight = criterion_eval.criterion.weight
                weighted_sum += criterion_eval.score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def update_overall_score(self) -> None:
        """Update the overall score based on criteria evaluations."""
        self.overall_score = self.calculate_overall_score()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "overall_score": self.overall_score,
            "summary": self.summary,
            "notes": self.notes,
            "is_published": self.is_published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "criteria_evaluations": [
                {
                    "criterion_name": ce.criterion.name if ce.criterion else "Unknown",
                    "score": ce.score,
                    "notes": ce.notes,
                }
                for ce in self.criterion_evaluations
            ],
        }