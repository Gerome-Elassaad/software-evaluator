import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from product_evaluator.utils.database import Base


class Criterion(Base):
    """Model for evaluation criteria used to assess products."""
    
    __tablename__ = "criteria"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    weight = Column(Integer, default=1, nullable=False)  # Importance weight for weighted averages
    is_default = Column(Boolean, default=False, nullable=False)  # Whether this is a default criterion
    prompt_template = Column(Text, nullable=True)  # Template for AI to evaluate this criterion
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships - using secondary relationships through CriterionEvaluation
    evaluations = relationship(
        "Evaluation", 
        secondary="criterion_evaluations", 
        back_populates="criteria"
    )
    
    def __repr__(self) -> str:
        return f"<Criterion {self.name}>"


class CriterionEvaluation(Base):
    """Association model linking criteria to evaluations with a score."""
    
    __tablename__ = "criterion_evaluations"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    criterion_id = Column(String(36), ForeignKey("criteria.id"), nullable=False)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False)
    score = Column(Integer, nullable=True)  # Score from 1-10
    notes = Column(Text, nullable=True)
    ai_generated_assessment = Column(Text, nullable=True)  # AI's assessment for this criterion
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    criterion = relationship("Criterion")
    evaluation = relationship("Evaluation", back_populates="criterion_evaluations")
    
    def __repr__(self) -> str:
        return f"<CriterionEvaluation {self.criterion.name if self.criterion else 'Unknown'}: {self.score}>"


# Insert default criteria
def create_default_criteria():
    """Create default evaluation criteria for the application."""
    default_criteria = [
        {
            "name": "Usability",
            "description": "How easy is the product to use? Consider the learning curve, user interface, and overall user experience.",
            "category": "User Experience",
            "weight": 3,
            "is_default": True,
            "prompt_template": "Evaluate the usability of this product. Consider user interface design, learning curve, documentation, and overall user experience. Provide specific strengths and weaknesses based on the available information."
        },
        {
            "name": "Performance",
            "description": "How well does the product perform its intended functions? Consider speed, efficiency, and resource usage.",
            "category": "Technical",
            "weight": 3,
            "is_default": True,
            "prompt_template": "Assess the performance characteristics of this product. Consider factors like speed, efficiency, scalability, and resource usage. Identify any performance limitations or strengths mentioned in the documentation or reviews."
        },
        {
            "name": "Documentation",
            "description": "How comprehensive and helpful is the product's documentation?",
            "category": "Support",
            "weight": 2,
            "is_default": True,
            "prompt_template": "Evaluate the quality and comprehensiveness of this product's documentation. Consider factors like clarity, completeness, examples, tutorials, and accessibility. Identify strengths and gaps in the documentation."
        },
        {
            "name": "Community & Support",
            "description": "What level of community engagement and official support is available?",
            "category": "Support",
            "weight": 2,
            "is_default": True,
            "prompt_template": "Assess the community and support ecosystem around this product. Consider factors like official support channels, response times, community size, forum activity, third-party resources, and overall helpfulness. Identify the strengths and limitations of the support available."
        },
        {
            "name": "Integration",
            "description": "How easily does the product integrate with other tools and platforms?",
            "category": "Technical",
            "weight": 2,
            "is_default": True,
            "prompt_template": "Evaluate how well this product integrates with other tools and platforms. Consider APIs, webhooks, plugins, extensibility, and compatibility with common technologies. Identify specific integrations mentioned and any integration limitations."
        },
        {
            "name": "Pricing",
            "description": "Is the pricing model fair and competitive for the value provided?",
            "category": "Business",
            "weight": 3,
            "is_default": True,
            "prompt_template": "Assess the pricing model and value proposition of this product. Consider factors like pricing structure, tiers, free plans, pricing compared to competitors, and overall value for money. Identify any limitations or benefits of the pricing approach."
        },
        {
            "name": "Security",
            "description": "How secure is the product? Consider data protection, compliance, and security features.",
            "category": "Technical",
            "weight": 3,
            "is_default": True,
            "prompt_template": "Evaluate the security aspects of this product. Consider data protection measures, compliance certifications, encryption, authentication, authorization controls, and security history. Identify specific security features or potential concerns."
        },
        {
            "name": "Scalability",
            "description": "How well does the product scale with increased usage or load?",
            "category": "Technical",
            "weight": 2,
            "is_default": True,
            "prompt_template": "Assess how well this product scales as usage grows. Consider performance under load, architectural limitations, handling of large data volumes, and documented scaling capabilities. Identify any scaling limitations or advantages mentioned."
        },
    ]
    
    from sqlalchemy.orm import Session
    from product_evaluator.utils.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if criteria already exist
        existing_count = db.query(Criterion).filter(Criterion.is_default == True).count()
        if existing_count == 0:
            # Insert default criteria
            for criterion_data in default_criteria:
                criterion = Criterion(**criterion_data)
                db.add(criterion)
            db.commit()
            print(f"Created {len(default_criteria)} default criteria")
        else:
            print(f"Default criteria already exist ({existing_count} found)")
    except Exception as e:
        db.rollback()
        print(f"Error creating default criteria: {e}")
    finally:
        db.close()