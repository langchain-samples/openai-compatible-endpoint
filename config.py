"""Configuration settings for the OpenAI-compatible server."""

import sys
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    openai_api_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> Settings:
    """Load and validate settings from environment."""
    try:
        return Settings()
    except Exception as e:
        print(f"Error: Could not load settings. Make sure OPENAI_API_KEY is set.")
        print(f"Details: {e}")
        sys.exit(1)

