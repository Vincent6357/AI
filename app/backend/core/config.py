"""
Configuration for the GCP RAG application
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # GCP Configuration
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GCP_LOCATION: str = "us"
    ENVIRONMENT: str = "dev"

    # Vertex AI Configuration
    VERTEX_AI_LOCATION: str = "us-central1"
    DEFAULT_MODEL: str = "gemini-1.5-pro"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Firebase Configuration
    FIREBASE_API_KEY: str = ""
    FIREBASE_AUTH_DOMAIN: str = ""
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_MESSAGING_SENDER_ID: str = ""
    FIREBASE_APP_ID: str = ""

    # Microsoft OAuth Configuration
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_TENANT_ID: str = ""

    # Auth settings
    USE_LOGIN: bool = False
    REQUIRE_ACCESS_CONTROL: bool = False
    ENABLE_UNAUTHENTICATED_ACCESS: bool = True

    # Storage Configuration
    MAIN_BUCKET_NAME: Optional[str] = None
    TEMP_UPLOADS_BUCKET: Optional[str] = None

    # Application Configuration
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md", ".html", ".csv"]

    # RAG Configuration
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 4096
    DEFAULT_TOP_K: int = 5
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.7

    # CORS Configuration - stored as string, converted to list
    CORS_ORIGINS: str = "*"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Service Account
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list"""
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
