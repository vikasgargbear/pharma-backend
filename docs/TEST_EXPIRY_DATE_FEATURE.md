# Testing Expiry Date Mandatory Feature

## Overview
This document explains how to test the "Expiry Date Mandatory" feature enforcement in the pharmaceutical ERP system.

## Test Scenarios

### 1. Check Current Feature Setting

First, verify the current setting in your Master Settings:

1. Open the frontend application
2. Go to Master Settings → Feature Settings
3. Check if "Expiry Date Mandatory" is enabled (it should be by default)

### 2. Test Product Creation with Batch

**Scenario A: Feature Enabled (Expiry Date Required)**

1. Keep "Expiry Date Mandatory" = ON
2. Try to create a new product with initial stock but NO expiry date
3. **Expected Result**: You should get an error: "Expiry date is mandatory for batch creation/update"

API Request Example:
```json
POST /api/v1/products
{
    "product_code": "TEST001",
    "product_name": "Test Medicine",
    "quantity_received": 100,
    // expiry_date is missing!
    "mrp": 100,
    "sale_price": 90,
    "cost_price": 80
}
```

**Scenario B: Feature Disabled (Expiry Date Optional)**

1. Turn OFF "Expiry Date Mandatory" in Feature Settings
2. Save the settings
3. Create the same product without expiry date
4. **Expected Result**: Product should be created successfully with a default expiry date (2 years from today)

### 3. Test Purchase Order Receiving

**Scenario A: Feature Enabled**

1. Create a purchase order
2. Try to receive items WITHOUT providing expiry dates
3. **Expected Result**: Error message: "Expiry date is mandatory for 'Product Name'. Please provide expiry date for all items being received."

API Request Example:
```json
POST /api/v1/purchases/{purchase_id}/receive-v2
{
    "items": [
        {
            "purchase_item_id": 1,
            "received_quantity": 50,
            // expiry_date is missing!
            "batch_number": "BATCH001"
        }
    ]
}
```

**Scenario B: Feature Disabled**

1. Turn OFF the feature
2. Receive the same items without expiry dates
3. **Expected Result**: Items should be received successfully

### 4. Frontend Validation

The frontend should also respect this setting:

1. **When Enabled**: Expiry date field should show as required (red asterisk)
2. **When Disabled**: Expiry date field should be optional

## How Feature Enforcement Works

### Backend Flow:

1. **API receives request** → Product creation or Purchase receiving
2. **Check organization features** → Get from `business_settings.features`
3. **Validate based on feature** → If `expiryDateMandatory` is true, check for expiry date
4. **Block or Allow** → Return error if mandatory and missing, otherwise proceed

### Code Locations:

1. **Feature Enforcement Module**: `/api/core/feature_enforcement.py`
2. **Product Creation**: `/api/routers/products.py` (line ~152)
3. **Purchase Receiving**: `/api/routers/v1/purchase_enhanced_v2.py` (line ~46)

## Verification in Database

After changing the feature setting, verify it's saved:

```sql
-- Check feature settings
SELECT business_settings->'features'->>'expiryDateMandatory' as expiry_mandatory
FROM organizations
WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f';

-- Check audit log
SELECT * FROM feature_change_log
WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
AND change_type = 'settings'
ORDER BY changed_at DESC
LIMIT 5;
```

## Common Issues

1. **Feature not enforcing**: Make sure backend is restarted after code changes
2. **Frontend not updating**: Clear browser cache or refresh the page
3. **Database not updating**: Check if the API endpoint is properly registered

## Summary

The expiry date mandatory feature demonstrates how organization-level settings can control business logic across the entire application. This same pattern can be applied to other features like:

- Allow Negative Stock
- Discount Limits
- Credit Limits
- Batch-wise Tracking
- Stock Adjustment Approval

Each feature is checked at the point of enforcement in the backend, ensuring data integrity regardless of frontend validation.