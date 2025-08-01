"""
Enterprise API v2 - Main Application
World-class pharmaceutical ERP API with direct schema mapping
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

# Import endpoint routers
from .endpoints.master import router as master_router
from .endpoints.parties import router as parties_router
from .endpoints.inventory import router as inventory_router
from .endpoints.sales import router as sales_router
from .endpoints.procurement import router as procurement_router
from .endpoints.financial import router as financial_router
from .endpoints.gst import router as gst_router
from .endpoints.compliance import router as compliance_router
from .endpoints.system import router as system_router
from .endpoints.analytics import router as analytics_router

# Import core modules
from .core.config import settings
from .core.database import database_manager
from .middleware.auth import AuthMiddleware
from .middleware.logging import LoggingMiddleware
from .middleware.error_handler import error_handler_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application metadata
API_VERSION = "2.0.0"
API_TITLE = "AASO Pharma ERP API v2"
API_DESCRIPTION = """
Enterprise-grade pharmaceutical ERP API with comprehensive features:

## 🎯 Key Features
- **Multi-tenant Architecture**: Organization-based data isolation
- **10 Specialized Schemas**: Direct mapping to database schemas
- **Type-Safe**: Full TypeScript/Pydantic support
- **GST Compliant**: E-invoicing, E-way bills, Returns
- **Real-time Analytics**: Dashboards and KPIs
- **Audit Trail**: Complete activity tracking
- **High Performance**: Optimized queries and caching

## 📚 API Modules
1. **Master**: Reference data management
2. **Parties**: Customer & Supplier management
3. **Inventory**: Product catalog & stock tracking
4. **Sales**: Order to cash workflow
5. **Procurement**: Purchase management
6. **Financial**: Payments & accounting
7. **GST**: Tax compliance
8. **Compliance**: Regulatory management
9. **System**: Configuration & settings
10. **Analytics**: Business intelligence
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info(f"🚀 Starting {API_TITLE} v{API_VERSION}")
    
    # Initialize database
    await database_manager.initialize()
    
    # Verify database schemas
    if await database_manager.verify_schemas():
        logger.info("✅ All database schemas verified")
    else:
        logger.warning("⚠️ Some database schemas missing")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down API")
    await database_manager.close()

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json",
    servers=[
        {"url": "/api/v2", "description": "API v2 Base URL"}
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(error_handler_middleware)
app.middleware("http")(LoggingMiddleware())
app.middleware("http")(AuthMiddleware())

# Include routers with schema-based prefixes
app.include_router(master_router, prefix="/api/v2/master", tags=["Master Data"])
app.include_router(parties_router, prefix="/api/v2/parties", tags=["Parties"])
app.include_router(inventory_router, prefix="/api/v2/inventory", tags=["Inventory"])
app.include_router(sales_router, prefix="/api/v2/sales", tags=["Sales Operations"])
app.include_router(procurement_router, prefix="/api/v2/procurement", tags=["Procurement"])
app.include_router(financial_router, prefix="/api/v2/financial", tags=["Financial"])
app.include_router(gst_router, prefix="/api/v2/gst", tags=["GST Compliance"])
app.include_router(compliance_router, prefix="/api/v2/compliance", tags=["Compliance"])
app.include_router(system_router, prefix="/api/v2/system", tags=["System"])
app.include_router(analytics_router, prefix="/api/v2/analytics", tags=["Analytics"])

# Root endpoint
@app.get("/api/v2", tags=["General"])
async def root():
    """API root endpoint with version information"""
    return {
        "success": True,
        "data": {
            "api": API_TITLE,
            "version": API_VERSION,
            "status": "operational",
            "documentation": "/api/v2/docs",
            "modules": [
                "master", "parties", "inventory", "sales", "procurement",
                "financial", "gst", "compliance", "system", "analytics"
            ]
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "version": API_VERSION
        }
    }

# Health check endpoint
@app.get("/api/v2/health", tags=["General"])
async def health_check():
    """System health check"""
    db_status = await database_manager.health_check()
    
    return {
        "success": True,
        "data": {
            "status": "healthy" if db_status else "degraded",
            "database": db_status,
            "api_version": API_VERSION,
            "timestamp": datetime.utcnow().isoformat()
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "version": API_VERSION
        }
    }

# Version endpoint
@app.get("/api/v2/version", tags=["General"])
async def version_info():
    """API version information"""
    return {
        "success": True,
        "data": {
            "api_version": API_VERSION,
            "supported_versions": ["2.0.0"],
            "deprecated_versions": [],
            "minimum_client_version": "2.0.0",
            "features": {
                "multi_tenant": True,
                "gst_compliance": True,
                "real_time_analytics": True,
                "audit_trail": True,
                "batch_operations": True,
                "field_selection": True,
                "advanced_filtering": True
            }
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "version": API_VERSION
        }
    }

# Custom exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "errors": [{
                "code": "NOT_FOUND",
                "message": f"Endpoint {request.url.path} not found"
            }],
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": API_VERSION
            }
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "errors": [{
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }],
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": API_VERSION
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_v2.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )