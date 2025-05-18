import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from product_evaluator.utils.database import Base


class Product(Base):
    """Product model for storing information about products being evaluated."""
    
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    vendor = Column(String(100), nullable=True, index=True)
    version = Column(String(50), nullable=True)
    price = Column(Float, nullable=True)
    pricing_model = Column(String(50), nullable=True)  # e.g., "one-time", "subscription", "freemium"
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Extracted data from the product website (populated by AI)
    extracted_content = Column(Text, nullable=True)
    extracted_features = Column(Text, nullable=True)
    
    # Relationships
    created_by = relationship("User", back_populates="products")
    evaluations = relationship("Evaluation", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Product {self.name}>"
    
    @property
    def average_rating(self) -> Optional[float]:
        """Calculate the average rating across all evaluations for this product."""
        if not self.evaluations:
            return None
        
        ratings = [evaluation.overall_score for evaluation in self.evaluations if evaluation.overall_score is not None]
        if not ratings:
            return None
        
        return sum(ratings) / len(ratings)
    
    @property
    def evaluation_count(self) -> int:
        """Get the number of evaluations for this product."""
        return len(self.evaluations)
    
    @property
    def summary(self) -> str:
        """Get a short summary of the product."""
        desc = self.description or ""
        if len(desc) > 100:
            return desc[:97] + "..."
        return desc