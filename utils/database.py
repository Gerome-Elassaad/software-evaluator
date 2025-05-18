from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from product_evaluator.config import settings, logger

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.APP_ENV == "development",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Create and yield a database session.
    This function should be used as a dependency in FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def initialize_db() -> None:
    """
    Initialize the database by creating all tables 
    (should be called at application startup).
    """
    logger.info("Initializing database...")
    try:
        # Import all models here to ensure they're registered with Base
        from product_evaluator.models.user.user_model import User  # noqa
        from product_evaluator.models.product.product_model import Product  # noqa
        from product_evaluator.models.evaluation.evaluation_model import Evaluation  # noqa
        from product_evaluator.models.evaluation.criteria_model import Criterion  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise