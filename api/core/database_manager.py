"""
World-class Database Connection Manager
Implements circuit breaker pattern, lazy connections, and graceful degradation
"""
import asyncio
import logging
import time
from typing import Optional
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import threading

logger = logging.getLogger(__name__)

class DatabaseCircuitBreaker:
    """Circuit breaker for database connections"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Check if we can execute database operations"""
        with self._lock:
            if self.state == "CLOSED":
                return True
            elif self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    return True
                return False
            else:  # HALF_OPEN
                return True
    
    def record_success(self):
        """Record successful operation"""
        with self._lock:
            self.failure_count = 0
            self.state = "CLOSED"
            logger.info("Database circuit breaker: SUCCESS - Circuit closed")
    
    def record_failure(self):
        """Record failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Database circuit breaker: OPEN - {self.failure_count} failures")
            else:
                logger.warning(f"Database circuit breaker: Failure {self.failure_count}/{self.failure_threshold}")

class DatabaseManager:
    """Production-ready database manager with lazy connections"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self.circuit_breaker = DatabaseCircuitBreaker()
        self.connection_pool_size = 2
        self.max_overflow = 5
        self.pool_timeout = 30
        self.pool_recycle = 300
        self._initialization_lock = threading.Lock()
        self._is_initialized = False
    
    def _create_engine(self):
        """Create database engine with optimized settings"""
        try:
            if self.database_url.startswith("postgresql"):
                # Convert to psycopg2 format
                url = self.database_url.replace("postgresql://", "postgresql+psycopg2://")
                
                # Add connection parameters for better reliability
                if "?" in url:
                    url += "&"
                else:
                    url += "?"
                url += "connect_timeout=10&application_name=pharma-backend"
                
                self.engine = create_engine(
                    url,
                    pool_size=self.connection_pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                # SQLite for development
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self._is_initialized = True
            logger.info("Database engine created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return False
    
    def initialize(self) -> bool:
        """Initialize database connection (lazy)"""
        if self._is_initialized:
            return True
            
        with self._initialization_lock:
            if self._is_initialized:
                return True
            return self._create_engine()
    
    def test_connection(self) -> bool:
        """Test database connection with circuit breaker"""
        if not self.circuit_breaker.can_execute():
            logger.warning("Database circuit breaker is OPEN - skipping connection test")
            return False
        
        try:
            if not self.initialize():
                self.circuit_breaker.record_failure()
                return False
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                self.circuit_breaker.record_success()
                return True
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            self.circuit_breaker.record_failure()
            return False
    
    def get_session(self):
        """Get database session with lazy initialization"""
        if not self.initialize():
            raise SQLAlchemyError("Database not initialized")
        
        if not self.circuit_breaker.can_execute():
            raise SQLAlchemyError("Database circuit breaker is OPEN")
        
        try:
            session = self.SessionLocal()
            # Test the session
            session.execute(text("SELECT 1"))
            self.circuit_breaker.record_success()
            return session
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise
    
    @asynccontextmanager
    async def get_session_async(self):
        """Async context manager for database sessions"""
        session = None
        try:
            session = self.get_session()
            yield session
        finally:
            if session:
                session.close()
    
    def get_health_status(self) -> dict:
        """Get comprehensive database health status"""
        try:
            is_connected = self.test_connection()
            
            return {
                "database": {
                    "status": "healthy" if is_connected else "unhealthy",
                    "connected": is_connected,
                    "circuit_breaker": {
                        "state": self.circuit_breaker.state,
                        "failure_count": self.circuit_breaker.failure_count,
                        "last_failure": self.circuit_breaker.last_failure_time
                    },
                    "connection_pool": {
                        "size": self.connection_pool_size,
                        "max_overflow": self.max_overflow,
                        "initialized": self._is_initialized
                    }
                }
            }
        except Exception as e:
            return {
                "database": {
                    "status": "error",
                    "error": str(e),
                    "connected": False
                }
            }

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        from .config import settings
        db_manager = DatabaseManager(settings.database_url)
    return db_manager

def get_db():
    """FastAPI dependency for database sessions"""
    db_manager = get_database_manager()
    
    try:
        session = db_manager.get_session()
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        # Raise HTTP exception for proper error handling
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=f"Database service temporarily unavailable: {str(e)}"
        )
    finally:
        if 'session' in locals():
            session.close()