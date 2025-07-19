# Backend Deployment Instructions

## Changes Made That Need Deployment

### 1. Product Search with Batch Information
**File**: `/api/routers/products.py`

The products endpoint has been updated to include:
- `batch_count`: Total number of batches for each product
- `available_batches`: Number of batches with stock > 0 and not expired
- `total_stock`: Total quantity available across all batches

**Key Changes**:
```python
# Added JOIN with batches table
# Added aggregation for stock counts
# Added org_id filtering
```

### 2. Customer Search with Area Field
**File**: `/api/routers/v1/customers.py`

The customer search now handles the optional 'area' field gracefully.

### 3. Invoice Service GST Calculations
**File**: `/api/services/invoice_service.py`

Updated to properly handle area field in customer addresses.

## Deployment Steps

1. **Commit and push the changes**:
```bash
git add -A
git commit -m "fix: Add batch information to product search, fix stock counts"
git push origin main
```

2. **Deploy to your hosting service** (Vercel/Railway/etc):
- The backend should automatically redeploy on push
- Or manually trigger deployment from your hosting dashboard

3. **Verify deployment**:
- Check the deployment logs for any errors
- Test the `/api/v1/products/?search=aaso` endpoint
- Verify response includes: `batch_count`, `available_batches`, `total_stock`

## Testing After Deployment

Open browser console and run:
```javascript
// Test product search with batch info
fetch('/api/v1/products/?search=aaso')
  .then(r => r.json())
  .then(data => console.log('Product data:', data));
```

The response should include fields like:
```json
{
  "product_id": 1,
  "product_name": "AasoTab",
  "batch_count": 2,
  "available_batches": 1,
  "total_stock": 100,
  ...
}
```

## If Stock Still Shows as "Out of Stock"

1. Check if batches exist in the database:
```sql
SELECT p.product_name, COUNT(b.batch_id), SUM(b.quantity_available)
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id
WHERE p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
GROUP BY p.product_id, p.product_name;
```

2. If no batches exist, create some test batches through the inventory management.

3. Check the browser console for the debug logs we added.