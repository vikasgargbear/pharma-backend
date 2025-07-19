"""
Version 1 API routers for enterprise pharma system
"""
from .customers import router as customers_router
from .orders import router as orders_router
from .inventory import router as inventory_router
from .billing import router as billing_router
from .payments import router as payments_router
from .invoices import router as invoices_router
from .order_items import router as order_items_router
from .users import router as users_router
from .suppliers import router as suppliers_router
from .purchases import router as purchases_router
from .delivery_challan import router as delivery_challan_router
from .dashboard import router as dashboard_router
from .sales_returns import router as sales_returns_router
from .stock_adjustments import router as stock_adjustments_router
from .tax_entries import router as tax_entries_router

__all__ = [
    "customers_router", 
    "orders_router", 
    "inventory_router", 
    "billing_router", 
    "payments_router", 
    "invoices_router",
    "order_items_router",
    "users_router", 
    "suppliers_router",
    "purchases_router",
    "delivery_challan_router",
    "dashboard_router",
    "sales_returns_router",
    "stock_adjustments_router",
    "tax_entries_router"
]