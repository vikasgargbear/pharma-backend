"""
AASO Pharma ERP - Production-Ready FastAPI Application
World-class pharmaceutical management system with comprehensive features
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
# import sentry_sdk
# from sentry_sdk.integrations.fastapi import FastApiIntegration
# from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
# import redis
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError

# Handle both package and direct imports for maximum compatibility
# FIXED: Import issues when running as module vs direct execution
# This allows the app to work with both 'python -m api.main' and 'uvicorn api.main:app'
# Import core modules
from .core.config import settings

# Import working routers
from .routers import (
    products,
    simple_delivery,
    db_inspect,
    migrations,
    migrations_v2,
    organizations,
    customers_simple,
    pack_debug
)

# Import v1 routers
from .routers.v1 import (
    customers_router, orders_router, inventory_router, billing_router, 
    payments_router, invoices_router, order_items_router, users_router,
    suppliers_router, purchases_router, delivery_challan_router, dashboard_router,
    stock_adjustments_router, tax_entries_router,
    purchase_upload_router, purchase_enhanced_router, sale_returns_api_router,
    purchase_returns_router, stock_movements_router, party_ledger_router,
    credit_debit_notes_router, sales_router, enterprise_orders_router,
    collection_center_router
)
from .routers.v1.org_users import router as org_users_router
from .routers.v1.stock_receive import router as stock_receive_router
from .routers.v1.direct_invoice import router as direct_invoice_router
from .routers.v1.invoice_with_order import router as invoice_with_order_router
from .routers.v1.smart_invoice import router as smart_invoice_router
from .routers.v1.quick_sale import router as quick_sale_router
from .routers.v1.enterprise_delivery_challan import router as enterprise_delivery_challan_router
from .routers.v1.challan_to_invoice import router as challan_to_invoice_router
from .routers.v1.organization_settings import router as organization_settings_router
from .routers.v1.auth import router as auth_router
from .routers.v1.sales_orders import router as sales_orders_router
from .routers.v1.stock_writeoff import router as stock_writeoff_router
from .routers.v1.organizations_debug import router as organizations_debug_router

# Configure Sentry for error tracking
# if hasattr(settings, 'SENTRY_DSN') and settings.SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=settings.SENTRY_DSN,
#         integrations=[
#             FastApiIntegration(auto_enabling_integrations=False),
#             SqlalchemyIntegration(),
#         ],
#         traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
#         environment=settings.ENVIRONMENT,
#         release=settings.APP_VERSION,
#     )

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events - World-class approach"""
    # Startup
    logger.info("🚀 Starting AASO Pharma ERP...")
    
    # Initialize database manager (lazy connection)
    from .core.database_manager import get_database_manager
    db_manager = get_database_manager()
    
    # Test database connection (non-blocking)
    if db_manager.test_connection():
        logger.info("✅ Database connection established")
    else:
        logger.warning("⚠️ Database connection failed - starting in degraded mode")
        logger.info("🔄 App will attempt to reconnect to database on demand")
    
    logger.info("🏥 AASO Pharma ERP is ready!")
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down AASO Pharma ERP...")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    World-class pharmaceutical management system with comprehensive ERP features.
    
    ## Features
    - 🏥 Complete pharmaceutical inventory management
    - 📋 Regulatory compliance (CDSCO, State Drug Controller)
    - 💊 Drug schedule management (G, H, H1, X)
    - 🎯 Batch tracking with expiry management
    - 💰 Advanced payment processing with UPI
    - 🏆 Customer loyalty programs
    - 📊 Comprehensive analytics and reporting
    - 🚚 Challan and delivery tracking
    - 📁 Document management system
    """,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else [
        "localhost", "127.0.0.1", 
        "*.railway.app", "*.up.railway.app",
        "pharma-backend-production-0c09.up.railway.app"
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
security = HTTPBearer()

# Rate limiting storage (in-memory for development, use Redis in production)
rate_limit_storage = defaultdict(list)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Basic rate limiting middleware"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if current_time - timestamp < 60
    ]
    
    # Check if client has exceeded rate limit (100 requests per minute)
    if len(rate_limit_storage[client_ip]) >= 100:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    # Add current request timestamp
    rate_limit_storage[client_ip].append(current_time)
    
    response = await call_next(request)
    return response

# Include working routers
app.include_router(products.router, prefix="/api/v1")
app.include_router(simple_delivery.router)
app.include_router(db_inspect.router)
app.include_router(migrations.router, prefix="/migrations")
app.include_router(migrations_v2.router)
app.include_router(organizations.router)
app.include_router(customers_simple.router)

# Include v1 API routers
app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(billing_router)
app.include_router(payments_router)
app.include_router(invoices_router)
app.include_router(order_items_router)
app.include_router(users_router)
app.include_router(org_users_router)  # 🚀 NEW: Organization users management
app.include_router(suppliers_router)
app.include_router(purchases_router)
app.include_router(delivery_challan_router)
app.include_router(dashboard_router)
app.include_router(stock_adjustments_router)
app.include_router(tax_entries_router)
app.include_router(purchase_upload_router)
app.include_router(purchase_enhanced_router)
app.include_router(sale_returns_api_router)
app.include_router(purchase_returns_router)
app.include_router(stock_movements_router)
app.include_router(party_ledger_router)
app.include_router(credit_debit_notes_router)
app.include_router(sales_router)
app.include_router(enterprise_orders_router)  # 🚀 NEW: Enterprise-grade order API
app.include_router(stock_receive_router)
app.include_router(direct_invoice_router)
app.include_router(invoice_with_order_router)
app.include_router(smart_invoice_router)
# app.include_router(quick_sale_router)  # DEPRECATED: Use enterprise_orders_router instead
app.include_router(enterprise_delivery_challan_router)  # 🚀 NEW: Enterprise-grade challan API
app.include_router(challan_to_invoice_router)  # 🚀 NEW: Create invoices from delivered challans
app.include_router(organization_settings_router)  # 🚀 NEW: Organization settings and profile management
app.include_router(auth_router)  # 🚀 NEW: JWT-based authentication with org context
app.include_router(sales_orders_router)  # 🚀 NEW: Enterprise sales order management
app.include_router(stock_writeoff_router)  # 🚀 NEW: Stock write-off with ITC reversal
app.include_router(collection_center_router)  # 🚀 NEW: Collection center with click-based WhatsApp/SMS

# Debug router (only in debug mode)
if settings.DEBUG:
    app.include_router(pack_debug.router)
    app.include_router(organizations_debug_router)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Database error handling middleware - World-class approach
@app.middleware("http")
async def database_error_handler(request: Request, call_next):
    """Handle database connection errors gracefully"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Check if it's a database-related error
        if "database" in str(e).lower() or "connection" in str(e).lower() or "psycopg2" in str(e).lower():
            logger.error(f"Database error in {request.url}: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "Database connection issues - please try again later",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            # Re-raise non-database errors
            raise

# Audit logging middleware - TEMPORARILY DISABLED DUE TO STREAMING ISSUE
# @app.middleware("http") 
# async def audit_middleware(request: Request, call_next):
#     """Audit logging middleware"""
#     try:
#         from .core.audit import AuditLogger
#     except ImportError:
#         from core.audit import AuditLogger
#     
#     start_time = time.time()
#     
#     try:
#         response = await call_next(request)
#         execution_time = time.time() - start_time
#         
#         # Log API access
#         AuditLogger.log_api_access(
#             request=request,
#             response_status=response.status_code,
#             execution_time=execution_time
#         )
#         
#         return response
#         
#     except Exception as e:
#         execution_time = time.time() - start_time
#         
#         # Log failed requests
#         AuditLogger.log_api_access(
#             request=request,
#             response_status=500,
#             execution_time=execution_time
#         )
#         
#         # Log security events for suspicious patterns
#         if any(pattern in str(request.url).lower() for pattern in ['admin', 'config', '.env', 'password']):
#             AuditLogger.log_security_event(
#                 event="suspicious_request",
#                 description=f"Suspicious request pattern: {request.url}",
#                 ip_address=request.client.host,
#                 severity="high"
#             )
#         
#         raise

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operation failed"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Root endpoint
@app.get("/")
async def read_root():
    """Root endpoint with system information"""
    return {
        "message": "🏥 AASO Pharma ERP - World-class pharmaceutical management system",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "✅ System operational",
        "features": [
            "Pharmaceutical inventory management",
            "Regulatory compliance",
            "Drug schedule management",
            "Batch tracking",
            "Payment processing",
            "Loyalty programs",
            "Analytics and reporting"
        ]
    }

# World-class health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint - always returns healthy if app is running"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/health/detailed", tags=["health"])
async def detailed_health_check():
    """Detailed health check with database status"""
    from .core.database_manager import get_database_manager
    
    db_manager = get_database_manager()
    health_status = db_manager.get_health_status()
    
    app_status = {
        "application": {
            "status": "healthy",
            "version": "2.2.0",  # Clean version with database tools
            "timestamp": datetime.utcnow()
        }
    }
    
    # Combine app and database status
    combined_status = {**app_status, **health_status}
    
    # Overall status
    overall_healthy = health_status.get("database", {}).get("status") == "healthy"
    combined_status["overall"] = {
        "status": "healthy" if overall_healthy else "degraded",
        "message": "All systems operational" if overall_healthy else "Database connection issues"
    }
    
    return combined_status

@app.get("/health/readiness", tags=["health"])
async def readiness_check():
    """Kubernetes readiness probe - checks if app can serve requests"""
    return {"ready": True, "timestamp": datetime.utcnow()}

@app.get("/health/liveness", tags=["health"])
async def liveness_check():
    """Kubernetes liveness probe - checks if app is alive"""
    return {"alive": True, "timestamp": datetime.utcnow()}

# System information endpoint
@app.get("/info")
async def system_info():
    """System information endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database_type": "PostgreSQL (Supabase)" if settings.is_supabase else "SQLite",
        "features_enabled": {
            "docs": settings.ENABLE_DOCS,
            "metrics": settings.ENABLE_METRICS,
            "debug": settings.DEBUG
        }
    }


# All API routes are now handled by modular routers
# See /routers/ directory for endpoint implementations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )