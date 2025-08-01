"""
API Compatibility Middleware
Handles field mappings between v1 frontend expectations and v2 backend
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any, Union, List

class CompatibilityMiddleware:
    """
    Middleware to handle API version compatibility
    Maps field names between frontend v1 expectations and backend v2 structure
    """
    
    # Field mappings: v1_field -> v2_field
    FIELD_MAPPINGS = {
        # Customer fields
        "outstanding_balance": "current_outstanding",
        "gstin": "gst_number",
        "contact_info": {
            "primary_phone": "primary_phone",
            "alternate_phone": "alternate_phone",
            "email": "email"
        },
        "address_info": {
            "billing_address": "billing_address",
            "billing_city": "billing_city",
            "billing_state": "billing_state",
            "billing_pincode": "billing_pincode",
            "shipping_address": "shipping_address",
            "shipping_city": "shipping_city",
            "shipping_state": "shipping_state",
            "shipping_pincode": "shipping_pincode"
        },
        
        # Supplier fields
        "supplier_gstin": "gst_number",
        "contact_person": "primary_contact_name",
        
        # Product fields
        "product_code": "item_code",
        "product_name": "item_name",
        
        # Invoice fields
        "invoice_type": "document_type",
        "party_id": "customer_id",
        
        # Common date fields
        "created": "created_at",
        "modified": "updated_at"
    }
    
    # Reverse mappings for requests: v2_field -> v1_field
    REVERSE_MAPPINGS = {
        "current_outstanding": "outstanding_balance",
        "gst_number": "gstin",
        "primary_phone": "contact_info.primary_phone",
        "email": "contact_info.email",
        "billing_address": "address_info.billing_address",
        "item_code": "product_code",
        "item_name": "product_name",
        "customer_id": "party_id",
        "created_at": "created",
        "updated_at": "modified"
    }
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # Store original request path
        is_v1_request = "/api/v1" in request.url.path
        
        # Process request body for v1 endpoints
        if is_v1_request and request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    # Map v1 fields to v2
                    mapped_data = self.map_request_fields(data)
                    # Create new request with mapped data
                    request._body = json.dumps(mapped_data).encode()
                except json.JSONDecodeError:
                    pass
        
        # Call the actual endpoint
        response = await call_next(request)
        
        # Process response for v1 endpoints
        if is_v1_request and hasattr(response, 'body'):
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                if body:
                    data = json.loads(body)
                    # Map v2 fields back to v1
                    mapped_data = self.map_response_fields(data)
                    
                    # Create new response with mapped data
                    return JSONResponse(
                        content=mapped_data,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
            except:
                # If mapping fails, return original response
                pass
        
        return response
    
    def map_request_fields(self, data: Union[Dict, List]) -> Union[Dict, List]:
        """Map v1 request fields to v2 structure"""
        if isinstance(data, list):
            return [self.map_request_fields(item) for item in data]
        
        if not isinstance(data, dict):
            return data
        
        mapped = {}
        
        for key, value in data.items():
            # Handle nested structures
            if key == "contact_info" and isinstance(value, dict):
                # Flatten contact_info
                for sub_key, sub_value in value.items():
                    mapped[sub_key] = sub_value
            elif key == "address_info" and isinstance(value, dict):
                # Flatten address_info
                for sub_key, sub_value in value.items():
                    mapped[sub_key] = sub_value
            elif key in self.FIELD_MAPPINGS:
                # Simple field mapping
                mapped[self.FIELD_MAPPINGS[key]] = value
            else:
                # Keep original field
                mapped[key] = value
        
        return mapped
    
    def map_response_fields(self, data: Union[Dict, List]) -> Union[Dict, List]:
        """Map v2 response fields to v1 structure"""
        if isinstance(data, list):
            return [self.map_response_fields(item) for item in data]
        
        if not isinstance(data, dict):
            return data
        
        # Handle standard response format
        if "data" in data:
            data["data"] = self.map_response_fields(data["data"])
            return data
        
        mapped = {}
        
        # Group fields for nested structures
        contact_info = {}
        address_info = {}
        
        for key, value in data.items():
            if key == "current_outstanding":
                mapped["outstanding_balance"] = value
            elif key == "gst_number":
                mapped["gstin"] = value
            elif key == "primary_phone":
                contact_info["primary_phone"] = value
            elif key == "alternate_phone":
                contact_info["alternate_phone"] = value
            elif key == "email":
                contact_info["email"] = value
            elif key.startswith("billing_"):
                address_info[key] = value
            elif key.startswith("shipping_"):
                address_info[key] = value
            else:
                # Keep original field
                mapped[key] = value
        
        # Add nested structures if they have data
        if contact_info:
            mapped["contact_info"] = contact_info
        if address_info:
            mapped["address_info"] = address_info
        
        return mapped

# Endpoint aliasing for different paths
ENDPOINT_ALIASES = {
    # Sales endpoints
    "/api/v1/sales/direct-invoice-sale": "/api/v2/sales/invoices/direct",
    "/api/v1/sales/invoices/search": "/api/v2/sales/invoices/search",
    
    # Purchase endpoints
    "/api/v1/purchases-enhanced": "/api/v2/procurement/purchases",
    "/api/v1/purchase-upload/parse-invoice-safe": "/api/v2/procurement/parse-invoice",
    
    # Inventory endpoints
    "/api/v1/inventory-movements": "/api/v2/inventory/movements",
    "/api/v1/inventory/stock-levels": "/api/v2/inventory/stock-levels",
    
    # Challan endpoints (orders with type)
    "/api/v1/orders": "/api/v2/sales/orders",
    "/api/v1/challans": "/api/v2/sales/delivery-challans",
}

def create_compatibility_middleware(app):
    """Factory function to create compatibility middleware"""
    return CompatibilityMiddleware(app)