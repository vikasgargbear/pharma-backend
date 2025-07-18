"""
Version 1 API routers for enterprise pharma system
"""
from .customers import router as customers_router
from .orders import router as orders_router
from .inventory import router as inventory_router
from .billing import router as billing_router
from .payments import router as payments_router

__all__ = ["customers_router", "orders_router", "inventory_router", "billing_router", "payments_router"]