import os
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_NAME: str = "Product Evaluator"
    
    # Database
    DATABASE_URL: str
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API keys for external services
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # AI settings
    AI_MODEL_NAME: str = "gemini-1.5-flash"  # Default model
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2048
    
    # Path settings
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "data" / "knowledge_base"
    EMBEDDINGS_DIR: Path = BASE_DIR / "data" / "embeddings"
    
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate and potentially modify the database URL."""
        if v.startswith("sqlite:///./"):
            # Convert relative path to absolute path
            sqlite_file = v.replace("sqlite:///./", "")
            return f"sqlite:///{BASE_DIR / sqlite_file}"
        return v
    
    def configure_logging(self) -> None:
        """Configure logging based on the application settings."""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()  # This will load variables from .env file

# Ensure required directories exist
settings.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
settings.EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
settings.configure_logging()

# Create application logger
logger = logging.getLogger("product_evaluator")