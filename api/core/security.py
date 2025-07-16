"""
Security utilities for error handling and logging
Simplified version for Phase 2 optimization
"""
import logging
import uuid
from typing import Optional
from datetime import datetime
from functools import wraps

from fastapi import HTTPException, Request, FastAPI
from fastapi.responses import JSONResponse

from .config import settings

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class ProductionException(HTTPException):
    """Custom exception with logging and error tracking"""
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code, detail)
        self.error_code = error_code
        self.error_id = str(uuid.uuid4())
        logger.error(f"API Error {status_code}: {detail} | Code: {error_code} | ID: {self.error_id}")


# Global exception handlers
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions"""
    error_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception: {exc} | Request: {request.url} | ID: {error_id}")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "server_error"
        }
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc} | Request: {request.url}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
            "type": "validation_error"
        }
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup all error handlers for the FastAPI application"""
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(ValueError, validation_exception_handler)
    app.add_exception_handler(ProductionException, lambda req, exc: JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "error_id": exc.error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "production_error"
        }
    ))


def handle_database_error(func):
    """Decorator to handle database errors gracefully"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs) if hasattr(func, '__call__') and func.__code__.co_flags & 0x80 else func(*args, **kwargs)
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(f"Database error in {func.__name__}: {e} | ID: {error_id}")
            raise ProductionException(
                status_code=500,
                detail=f"Database operation failed: {str(e)}",
                error_code="DATABASE_ERROR"
            )
    return wrapper


# Common business exceptions
class InsufficientStockError(ProductionException):
    def __init__(self, product_name: str, requested: int, available: int):
        super().__init__(
            status_code=400,
            detail=f"Insufficient stock for {product_name}. Requested: {requested}, Available: {available}",
            error_code="INSUFFICIENT_STOCK"
        )


class InvalidCredentialsError(ProductionException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Invalid credentials",
            error_code="INVALID_CREDENTIALS"
        )


class PermissionDeniedError(ProductionException):
    def __init__(self, action: str):
        super().__init__(
            status_code=403,
            detail=f"Permission denied for action: {action}",
            error_code="PERMISSION_DENIED"
        )


class ResourceNotFoundError(ProductionException):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            status_code=404,
            detail=f"{resource} with ID {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND"
        ) 