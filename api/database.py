"""
Database Configuration - Supabase (PostgreSQL) Compatible
Enhanced with connection pooling and production optimizations
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Handle both package and direct imports
try:
    from .core.config import settings
except ImportError:
    from core.config import settings

# Get database URL from settings (supports both SQLite and PostgreSQL/Supabase)
SQLALCHEMY_DATABASE_URL = settings.database_url

# Create the engine with optimized settings
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for development
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG  # Enable SQL logging in debug mode
    )
else:
    # PostgreSQL/Supabase configuration for production
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=False  # FIXED: Disabled SQL logging for better performance (was causing verbose logs)
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database health check
def check_database_connection():
    """Check if database connection is working"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # Try to execute a simple query
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Database initialization
def init_database():
    """Initialize database tables"""
    try:
        from . import models
    except ImportError:
        import models
    
    # FIXED: Skip table creation for PostgreSQL/Supabase (tables already exist)
    # This optimization prevents SQLAlchemy from checking all tables during startup
    # which was causing long startup times
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        print(f"✅ Using existing PostgreSQL tables: {settings.database_url[:50]}...")
        print(f"📊 Connection pool size: {settings.DB_POOL_SIZE}")
        print(f"🔄 Database type: PostgreSQL (Supabase)")
    else:
        Base.metadata.create_all(bind=engine)
        print(f"✅ Database initialized: {settings.database_url}")
        print(f"📊 Connection pool size: {settings.DB_POOL_SIZE}")
        print(f"🔄 Database type: SQLite")

# Export for use in other modules
__all__ = ["engine", "SessionLocal", "Base", "get_db", "check_database_connection", "init_database"]


