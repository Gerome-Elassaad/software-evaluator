import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import bcrypt
from product_evaluator.utils.database import Base


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="created_by", cascade="all, delete-orphan")
    
    @classmethod
    def create(cls, username: str, email: str, password: str, full_name: Optional[str] = None) -> "User":
        """Create a new user with hashed password."""
        hashed_password = cls.hash_password(password)
        return cls(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        password_bytes = password.encode('utf-8')
        hashed_bytes = self.hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    def update_password(self, new_password: str) -> None:
        """Update the user's password."""
        self.hashed_password = self.hash_password(new_password)
        self.updated_at = datetime.now()
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"