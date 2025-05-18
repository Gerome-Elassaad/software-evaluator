#!/usr/bin/env python
"""
Startup script for the Product Evaluator application.
This script initializes the database and creates a demo admin user if none exists.
"""

import os
import sys
import argparse
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from product_evaluator.config import settings
from product_evaluator.utils.database import initialize_db, SessionLocal
from product_evaluator.models.user.user_model import User
from product_evaluator.models.evaluation.criteria_model import create_default_criteria


def create_demo_user(db: Session, username: str, password: str) -> None:
    """
    Create a demo admin user if it doesn't exist.
    
    Args:
        db: Database session
        username: Username for the demo user
        password: Password for the demo user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    
    if existing_user:
        print(f"Demo user '{username}' already exists.")
        return
    
    # Create user
    user = User.create(
        username=username,
        email=f"{username}@example.com",
        password=password,
        full_name="Demo Admin"
    )
    
    # Set as admin
    user.is_admin = True
    
    # Add to database
    db.add(user)
    db.commit()
    
    print(f"Demo admin user '{username}' created successfully!")


def setup_demo_data(db: Session) -> None:
    """
    Set up demo data for the application.
    
    Args:
        db: Database session
    """
    from product_evaluator.models.product.product_model import Product
    
    # Check if we already have products
    existing_products = db.query(Product).count()
    
    if existing_products > 0:
        print(f"Demo data already exists ({existing_products} products found).")
        return
    
    # Get admin user
    admin_user = db.query(User).filter(User.username == 'admin').first()
    
    if not admin_user:
        print("Admin user not found. Cannot create demo data.")
        return
    
    # Create demo products
    demo_products = [
        {
            "name": "FastAPI",
            "description": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.",
            "website_url": "https://fastapi.tiangolo.com/",
            "category": "Framework/Library",
            "vendor": "Tiangolo",
            "version": "0.95.0",
            "pricing_model": "free",
            "created_by_id": admin_user.id
        },
        {
            "name": "PostgreSQL",
            "description": "PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development that has earned it a strong reputation for reliability, feature robustness, and performance.",
            "website_url": "https://www.postgresql.org/",
            "category": "Infrastructure",
            "vendor": "PostgreSQL Global Development Group",
            "version": "14.5",
            "pricing_model": "free",
            "created_by_id": admin_user.id
        },
        {
            "name": "TailwindCSS",
            "description": "A utility-first CSS framework packed with classes like flex, pt-4, text-center and rotate-90 that can be composed to build any design, directly in your markup.",
            "website_url": "https://tailwindcss.com/",
            "category": "Framework/Library",
            "vendor": "Tailwind Labs",
            "version": "3.3.0",
            "pricing_model": "freemium",
            "created_by_id": admin_user.id
        }
    ]
    
    for product_data in demo_products:
        product = Product(**product_data)
        db.add(product)
    
    db.commit()
    print(f"Created {len(demo_products)} demo products!")


def main(args: argparse.Namespace) -> None:
    """
    Main function to setup the application.
    
    Args:
        args: Command line arguments
    """
    print("Initializing Product Evaluator...")
    
    # Initialize database
    initialize_db()
    print("Database initialized successfully!")
    
    # Create default criteria
    create_default_criteria()
    
    # Create demo user
    db = SessionLocal()
    try:
        create_demo_user(db, args.username, args.password)
        
        # Set up demo data if requested
        if args.demo_data:
            setup_demo_data(db)
    finally:
        db.close()
    
    print("Startup completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the Product Evaluator application")
    parser.add_argument("--username", default="admin", help="Username for demo admin user")
    parser.add_argument("--password", default="password", help="Password for demo admin user")
    parser.add_argument("--demo-data", action="store_true", help="Create demo data")
    
    args = parser.parse_args()
    
    main(args)