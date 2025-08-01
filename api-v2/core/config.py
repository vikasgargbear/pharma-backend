"""
Core Configuration for Enterprise API v2
Environment-based settings with type safety
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v2"
    PROJECT_NAME: str = "AASO Pharma ERP API v2"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://user:pass@localhost/pharma_erp",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # Security Configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    JWT_REFRESH_EXPIRATION_DAYS: int = Field(default=30, env="JWT_REFRESH_EXPIRATION_DAYS")
    BCRYPT_ROUNDS: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "https://pharma-frontend.up.railway.app"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_UPLOAD_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "application/pdf"],
        env="ALLOWED_UPLOAD_TYPES"
    )
    
    # Cache Configuration
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    
    # Email Configuration
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@aasopharma.com", env="EMAIL_FROM")
    
    # SMS Configuration
    SMS_API_KEY: Optional[str] = Field(default=None, env="SMS_API_KEY")
    SMS_SENDER_ID: str = Field(default="AASOPH", env="SMS_SENDER_ID")
    
    # WhatsApp Configuration
    WHATSAPP_API_KEY: Optional[str] = Field(default=None, env="WHATSAPP_API_KEY")
    WHATSAPP_API_URL: Optional[str] = Field(default=None, env="WHATSAPP_API_URL")
    
    # GST API Configuration
    GST_API_URL: str = Field(
        default="https://api.gst.gov.in",
        env="GST_API_URL"
    )
    GST_CLIENT_ID: Optional[str] = Field(default=None, env="GST_CLIENT_ID")
    GST_CLIENT_SECRET: Optional[str] = Field(default=None, env="GST_CLIENT_SECRET")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Performance Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    APM_ENABLED: bool = Field(default=False, env="APM_ENABLED")
    
    # Feature Flags
    FEATURE_GST_ENABLED: bool = Field(default=True, env="FEATURE_GST_ENABLED")
    FEATURE_EINVOICE_ENABLED: bool = Field(default=True, env="FEATURE_EINVOICE_ENABLED")
    FEATURE_ANALYTICS_ENABLED: bool = Field(default=True, env="FEATURE_ANALYTICS_ENABLED")
    FEATURE_AUDIT_TRAIL: bool = Field(default=True, env="FEATURE_AUDIT_TRAIL")
    
    # Business Configuration
    DEFAULT_CURRENCY: str = Field(default="INR", env="DEFAULT_CURRENCY")
    DEFAULT_COUNTRY: str = Field(default="IN", env="DEFAULT_COUNTRY")
    DEFAULT_TIMEZONE: str = Field(default="Asia/Kolkata", env="DEFAULT_TIMEZONE")
    FISCAL_YEAR_START: str = Field(default="04-01", env="FISCAL_YEAR_START")  # MM-DD
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Environment-specific configurations
if settings.DEBUG:
    settings.LOG_LEVEL = "DEBUG"
    settings.BCRYPT_ROUNDS = 4  # Faster for development

# Export commonly used values
SECRET_KEY = settings.SECRET_KEY
DATABASE_URL = settings.DATABASE_URL
DEBUG = settings.DEBUG