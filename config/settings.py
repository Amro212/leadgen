"""
Configuration and environment settings loader.
Loads environment variables from .env and provides centralized settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional


# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Directories
    OUTPUT_DIR: Path = Path("./output")
    LOG_DIR: Path = Path("./logs")
    
    # API Keys (optional)
    GOOGLE_API_KEY: Optional[str] = None
    YELP_API_KEY: Optional[str] = None
    HUNTER_API_KEY: Optional[str] = None
    CLEARBIT_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Database (optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Rate limiting
    REQUEST_DELAY: float = 1.5  # seconds between requests
    REQUEST_TIMEOUT: int = 8  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
SETTINGS = Settings()


# Ensure output and log directories exist
SETTINGS.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS.LOG_DIR.mkdir(parents=True, exist_ok=True)
