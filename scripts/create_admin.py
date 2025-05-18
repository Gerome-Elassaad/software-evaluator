"""
Script to create an admin user in the database.
Run this script after initializing the database to create the first admin user.
"""

import os
import sys
import argparse
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_evaluator.config import settings
from product_evaluator.models.user.user_model import User
from product_evaluator.utils.database import Base


def create_admin_user(
    username: str, 
    email: str, 
    password: str, 
    full_name: str = "Admin User",
    db_url: str = None
) -> None:
    """
    Create an admin user in the database.
    
    Args:
        username: Admin username
        email: Admin email
        password: Admin password
        full_name: Admin full name
        db_url: Database URL (defaults to settings.DATABASE_URL)
    """
    # Use provided DB URL or fall back to settings
    db_url = db_url or settings.DATABASE_URL
    
    # Create engine and session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists.")
            return
        
        # Create user
        user = User.create(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
        )
        
        # Set as admin
        user.is_admin = True
        
        # Add to database
        db.add(user)
        db.commit()
        
        print(f"Admin user '{username}' created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user in the database.")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--full-name", default="Admin User", help="Admin full name")
    parser.add_argument("--db-url", help="Database URL (defaults to settings.DATABASE_URL)")
    
    args = parser.parse_args()
    
    create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name,
        db_url=args.db_url
    )