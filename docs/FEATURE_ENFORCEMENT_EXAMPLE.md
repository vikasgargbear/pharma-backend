# Feature Enforcement Example: Allow Negative Billing

## What is Negative Billing?

In pharmaceutical retail, "negative billing" means allowing sales even when stock is not available (stock goes negative). This is common because:

1. **Emergency Medicine**: Patient needs critical medicine immediately
2. **Stock in Transit**: New stock arriving soon (same day/next day)
3. **Stock Counting Errors**: Physical stock exists but system shows zero
4. **Inter-branch Transfer**: Stock available at another branch

## How Feature Enforcement Works

### 1. Frontend Check (User Experience)
```javascript
// In Sales component
const createSale = async (saleData) => {
  const features = await getOrganizationFeatures();
  
  if (!features.allowNegativeStock && product.available_quantity < quantity) {
    showError("Insufficient stock. Negative billing is not allowed.");
    return;
  }
  
  // Proceed with sale
}
```

### 2. Backend Enforcement (Security)
```python
# In sales endpoint
@router.post("/sales")
async def create_sale(sale_data: Dict, db: Session = Depends(get_db)):
    # Get organization features
    org_features = get_org_features(current_org["org_id"])
    
    # Check each item
    for item in sale_data["items"]:
        product = db.query(Product).filter_by(product_id=item["product_id"]).first()
        
        # Feature enforcement
        if not org_features.get("allowNegativeStock", False):
            if product.available_quantity < item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.product_name}. "
                           f"Available: {product.available_quantity}, "
                           f"Requested: {item['quantity']}"
                )
        
        # Update stock (can go negative if allowed)
        product.available_quantity -= item["quantity"]
    
    # Create sale record
    sale = Sale(**sale_data)
    db.add(sale)
    db.commit()
```

### 3. Database Level Constraint (Optional)
```sql
-- Add check constraint based on organization settings
CREATE OR REPLACE FUNCTION check_stock_levels()
RETURNS TRIGGER AS $$
DECLARE
    allow_negative BOOLEAN;
BEGIN
    -- Get organization setting
    SELECT (business_settings->>'allowNegativeStock')::boolean 
    INTO allow_negative
    FROM organizations 
    WHERE org_id = NEW.org_id;
    
    -- Enforce if negative not allowed
    IF NOT COALESCE(allow_negative, false) AND NEW.available_quantity < 0 THEN
        RAISE EXCEPTION 'Negative stock not allowed for this organization';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_stock_levels
    BEFORE UPDATE ON products
    FOR EACH ROW
    WHEN (NEW.available_quantity < OLD.available_quantity)
    EXECUTE FUNCTION check_stock_levels();
```

## Feature Configuration Options

### Simple Boolean (Current)
```json
{
  "allowNegativeStock": true
}
```

### Advanced Configuration
```json
{
  "allowNegativeStock": {
    "enabled": true,
    "requiresApproval": true,
    "maxNegativeLimit": -100,
    "allowedCategories": ["life-saving", "critical"],
    "notificationThreshold": -10,
    "autoBlockAfterDays": 7
  }
}
```

## Pros/Cons of Current vs Separate Table

### Current Design (JSONB in organizations table)
**Pros:**
- Simple and fast queries
- Flexible schema evolution
- Easy to add new features
- Single source of truth

**Cons:**
- No audit trail
- Harder to query across organizations
- No feature versioning

### Separate Features Table
**Pros:**
- Full audit trail
- Feature history/versioning
- Better for analytics
- Can have feature dependencies

**Cons:**
- More complex queries
- Potential performance impact
- More tables to manage

## Recommendation

For a pharmaceutical ERP, the current JSONB approach is sufficient because:

1. **Performance**: Features are loaded once per session
2. **Simplicity**: Easy to understand and maintain
3. **Flexibility**: Can add complex features without schema changes
4. **Real-world usage**: Most pharmacies set features once and rarely change

However, if you need:
- Audit compliance (who changed what, when)
- Feature A/B testing
- Time-based features
- Complex feature dependencies

Then a separate table would be better.

## Implementation Checklist

1. ✅ Store features in organization (current design)
2. ✅ Frontend reads features on login/load
3. ✅ Frontend provides UI feedback
4. ⚠️  Backend enforces at API level
5. ⚠️  Optional: Database constraints
6. ⚠️  Audit logging for changes
7. ⚠️  Feature documentation for users