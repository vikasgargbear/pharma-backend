"""
Version 1 API routers for enterprise pharma system
"""
from .customers import router as customers_router
from .orders import router as orders_router

__all__ = ["customers_router", "orders_router"]