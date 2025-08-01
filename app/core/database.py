"""
Database configuration with connection resilience
"""
import os
import logging
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import time

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fix for Supabase connection issues
if "supabase.co" in DATABASE_URL:
    # Add connection parameters for better reliability
    if "?" in DATABASE_URL:
        DATABASE_URL += "&"
    else:
        DATABASE_URL += "?"
    
    # Add connection parameters
    DATABASE_URL += "sslmode=require&connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"
    
    # If using port 5432, suggest using pooler port 6543
    if ":5432/" in DATABASE_URL:
        logger.warning("Using direct connection port 5432. Consider using pooler port 6543 for better reliability.")

# Create engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    # Use NullPool to avoid connection pooling issues with Supabase
    poolclass=NullPool,
    # Connection pool settings
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "options": "-c statement_timeout=30000"  # 30 second statement timeout
    }
)

# Add connection retry logic
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    connection_record.info['connect_time'] = time.time()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    # Invalidate connection if it's been idle for too long
    timeout = time.time() - connection_record.info.get('connect_time', 0)
    if timeout > 300:  # 5 minutes
        connection_proxy.invalidate()
        raise Exception("Connection invalidated due to timeout")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """
    Test database connection
    """
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False