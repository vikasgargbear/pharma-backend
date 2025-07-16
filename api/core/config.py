"""
Production Configuration Settings
Enhanced with Supabase (PostgreSQL) support
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    # Database - Supabase Compatible (Railway compatible)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/pharma_prod.db")
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Auto-configure for Supabase if URL is provided
    @property
    def is_supabase(self) -> bool:
        """Check if we're using Supabase"""
        return self.DATABASE_URL.startswith("postgresql://") or (self.SUPABASE_URL is not None and "supabase.co" in self.SUPABASE_URL)
    
    @property
    def database_url(self) -> str:
        """Get the appropriate database URL"""
        # Use the DATABASE_URL if it's set and is a postgresql URL
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
        return self.DATABASE_URL
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # CORS - Enhanced for production
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000", 
        "http://localhost:3001",
        "https://your-domain.com",  # Add your production domain
        "https://app.supabase.io"  # Supabase dashboard
    ]
    
    # Database Connection Pool (Memory optimized for Render)
    DB_POOL_SIZE: int = 2 if os.getenv("DATABASE_URL", "").startswith("postgresql") else 2
    DB_MAX_OVERFLOW: int = 5 if os.getenv("DATABASE_URL", "").startswith("postgresql") else 0
    DB_POOL_RECYCLE: int = 3600  # 1 hour for PostgreSQL
    DB_POOL_PRE_PING: bool = True  # Enable connection health checks
    
    # Redis Cache
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_EXPIRE_SECONDS: int = 300
    
    # File Upload - Supabase Storage compatible
    UPLOAD_PATH: str = "./uploads"
    SUPABASE_STORAGE_BUCKET: str = "pharma-uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: list = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    
    # Email
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # WhatsApp (Business API)
    WHATSAPP_TOKEN: Optional[str] = os.getenv("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    # UPI
    UPI_MERCHANT_ID: str = os.getenv("UPI_MERCHANT_ID", "pharmacy@hdfc")
    UPI_MERCHANT_NAME: str = os.getenv("UPI_MERCHANT_NAME", "Pharma Wholesale Ltd")
    
    # Application
    APP_NAME: str = "Pharma Management System"
    APP_VERSION: str = "2.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Error Tracking
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Production Optimizations
    ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "True").lower() == "true"
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """Parse environment variables with type conversion"""
            if field_name == 'ALLOWED_ORIGINS':
                return [origin.strip() for origin in raw_val.split(',')]
            elif field_name == 'ALLOWED_FILE_TYPES':
                return [ext.strip() for ext in raw_val.split(',')]
            return raw_val


# Singleton instance
settings = Settings()

# Supabase helper functions
def get_supabase_client():
    """Get Supabase client if configured"""
    if settings.is_supabase:
        try:
            from supabase import create_client, Client
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except ImportError:
            print("⚠️  Supabase client not installed. Run: pip install supabase")
            return None
    return None

def get_database_info():
    """Get database configuration info"""
    return {
        "type": "PostgreSQL (Supabase)" if settings.is_supabase else "SQLite",
        "url": settings.database_url,
        "pool_size": settings.DB_POOL_SIZE,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    } 