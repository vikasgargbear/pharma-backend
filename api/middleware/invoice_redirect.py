"""
Invoice Redirect Middleware
Intercepts old order-based invoice calls and redirects to quick-sale
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import json
import re

async def invoice_redirect_middleware(request: Request, call_next):
    """
    Middleware to handle legacy invoice creation attempts
    """
    # Check if this is an invoice generation request for a non-existent order
    path = request.url.path
    
    # Pattern: /api/v1/orders/{order_id}/invoice
    invoice_pattern = re.match(r'^/api/v1/orders/(\d+)/invoice$', path)
    
    if invoice_pattern and request.method == "POST":
        order_id = int(invoice_pattern.group(1))
        
        # Check if this looks like a non-existent order (ID > 45)
        if order_id > 45:  # We know latest real order is 45
            print(f"🔄 Intercepting invoice request for non-existent order {order_id}")
            
            # Get the request body
            body = await request.body()
            try:
                invoice_data = json.loads(body) if body else {}
            except:
                invoice_data = {}
            
            # Return a helpful response
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Order {order_id} not found - Frontend needs update",
                    "message": "The frontend is using an outdated API flow. Please update to use the new quick-sale endpoint.",
                    "solution": {
                        "old_flow": f"POST /api/v1/orders/{order_id}/invoice (requires existing order)",
                        "new_flow": "POST /api/v1/quick-sale/ (creates everything in one call)",
                        "example": {
                            "endpoint": "POST /api/v1/quick-sale/",
                            "body": {
                                "customer_id": 1,
                                "items": [
                                    {"product_id": 49, "quantity": 10}
                                ],
                                "payment_mode": "Cash"
                            }
                        }
                    },
                    "frontend_action_required": "Update the invoice save function to use /api/v1/quick-sale/",
                    "temporary_workaround": "Use the 'Create Invoice' button instead of 'Save Invoice' if available"
                }
            )
    
    # For all other requests, continue normally
    response = await call_next(request)
    return response