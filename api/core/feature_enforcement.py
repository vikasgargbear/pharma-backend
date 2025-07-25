"""
Feature Enforcement Module
Provides functions to check organization features and enforce them
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

def get_organization_features(db: Session, org_id: str) -> Dict[str, Any]:
    """
    Get organization features from business_settings
    Returns default features if not set
    """
    result = db.execute(text("""
        SELECT business_settings
        FROM organizations
        WHERE org_id = :org_id
    """), {"org_id": org_id}).fetchone()
    
    if not result or not result.business_settings:
        return get_default_features()
    
    # Extract features from business_settings
    features = result.business_settings.get("features", {})
    
    # Merge with defaults to ensure all features have values
    default_features = get_default_features()
    default_features.update(features)
    
    return default_features

def get_default_features() -> Dict[str, Any]:
    """
    Get default feature settings
    """
    return {
        # Inventory Features
        "allowNegativeStock": False,
        "expiryDateMandatory": True,
        "batchWiseTracking": True,
        "stockAdjustmentApproval": False,
        "lowStockAlerts": True,
        
        # Sales Features
        "creditLimitForParties": True,
        "creditLimitThreshold": 100000,
        "salesReturnFlow": "with-credit-note",
        "salesApprovalRequired": False,
        "discountLimit": 20,
        
        # Purchase Features
        "grnWorkflow": True,
        "purchaseApprovalLimit": 50000,
        "autoGeneratePurchaseOrder": False,
        "vendorRatingSystem": False,
        
        # E-Way Bill
        "ewayBillEnabled": True,
        "ewayBillThreshold": 50000,
        "autoGenerateEwayBill": False,
        
        # GST Features
        "gstRoundOff": True,
        "reverseChargeApplicable": False,
        "compositionScheme": False,
        "tcsApplicable": False,
        
        # Payment Features
        "allowPartialPayments": True,
        "autoReconciliation": False,
        "paymentReminders": True,
        "reminderDays": [7, 15, 30],
        
        # General Features
        "multiCurrency": False,
        "multiLocation": True,
        "barcodeScannerIntegration": False,
        "smsNotifications": False,
        "emailNotifications": True,
        "whatsappNotifications": False,
        
        # Security Features
        "twoFactorAuth": False,
        "ipRestriction": False,
        "sessionTimeout": 30,
        "passwordComplexity": "medium",
        
        # Workflow Features
        "purchaseWorkflow": True,
        "salesWorkflow": False,
        "paymentApproval": True,
        "returnApproval": True
    }

def enforce_expiry_date_mandatory(
    features: Dict[str, Any], 
    expiry_date: Optional[Any],
    context: str = "product"
) -> None:
    """
    Enforce expiry date mandatory feature
    Raises HTTPException if expiry date is required but not provided
    
    Args:
        features: Organization features dict
        expiry_date: The expiry date value
        context: Context for error message (e.g., "product", "batch", "purchase")
    """
    if features.get("expiryDateMandatory", True) and not expiry_date:
        raise HTTPException(
            status_code=400,
            detail=f"Expiry date is mandatory for {context} creation/update. "
                   f"Please provide an expiry date."
        )

def enforce_negative_stock(
    features: Dict[str, Any],
    current_stock: float,
    requested_quantity: float,
    product_name: str = "product"
) -> None:
    """
    Enforce negative stock feature
    Raises HTTPException if negative stock is not allowed
    """
    if not features.get("allowNegativeStock", False):
        if current_stock < requested_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product_name}. "
                       f"Available: {current_stock}, Requested: {requested_quantity}. "
                       f"Negative stock is not allowed."
            )

def enforce_discount_limit(
    features: Dict[str, Any],
    discount_percent: float,
    line_item: str = ""
) -> None:
    """
    Enforce discount limit feature
    Raises HTTPException if discount exceeds limit
    """
    max_discount = features.get("discountLimit", 100)
    
    if discount_percent > max_discount:
        item_context = f" for {line_item}" if line_item else ""
        raise HTTPException(
            status_code=400,
            detail=f"Discount{item_context} exceeds the maximum allowed limit of {max_discount}%"
        )

def enforce_credit_limit(
    features: Dict[str, Any],
    customer_credit_limit: Optional[float],
    order_amount: float,
    customer_name: str = "customer"
) -> None:
    """
    Enforce credit limit feature
    Raises HTTPException if credit limit is exceeded
    """
    if features.get("creditLimitForParties", True):
        # Use customer's specific limit or default threshold
        credit_limit = customer_credit_limit or features.get("creditLimitThreshold", 100000)
        
        if order_amount > credit_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Order amount ({order_amount}) exceeds credit limit ({credit_limit}) "
                       f"for {customer_name}"
            )