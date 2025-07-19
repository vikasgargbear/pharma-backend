# API Test Results - AASO Pharma ERP

## Test Date: 2025-07-19

### Summary
All API endpoints have been successfully tested locally. The unified inventory movements approach is working correctly.

### Test Results

#### 1. Sales Returns API ✅
- **Endpoint**: `POST /api/v1/sales-returns/`
- **Test Data**: Order #38, Product #14, Batch #4, Quantity: 2
- **Result**: Successfully created movement ID 55
- **Inventory Impact**: Stock increased back by 2 units
- **Reference**: SR-38-202507182054

#### 2. Stock Adjustments API ✅
- **Endpoint**: `POST /api/v1/stock-adjustments/`
- **Test Type**: Damage adjustment
- **Test Data**: Batch #4, Quantity: -3 (damaged units)
- **Result**: Successfully created movement ID 56
- **Inventory Impact**: Stock reduced from 794 to 791
- **Movement Type**: stock_damage

#### 3. Physical Count API ✅
- **Endpoint**: `POST /api/v1/stock-adjustments/physical-count`
- **Test Data**: Batch #4, Counted: 790 (System showed 791)
- **Result**: Created adjustment for -1 unit difference
- **Movement ID**: 57
- **Movement Type**: stock_count

#### 4. Expire Batches API ✅
- **Endpoint**: `POST /api/v1/stock-adjustments/expire-batches`
- **Result**: Found and expired 1 batch
- **Expired Batch**: #6 (222 units of "Aaso New Test2")
- **Movement ID**: 58
- **Movement Type**: stock_expiry

#### 5. Tax Calculation API ✅
- **Endpoint**: `POST /api/v1/tax-entries/calculate`
- **Intrastate Test**: ₹1000 @ 12% = ₹60 CGST + ₹60 SGST = ₹120 total tax
- **Interstate Test**: ₹1000 @ 18% = ₹180 IGST
- **Result**: Calculations are accurate

### Database Impact
All operations correctly created entries in the `inventory_movements` table:
- Movement types are properly set (sales_return, stock_damage, stock_count, stock_expiry)
- Batch quantities are automatically updated
- Audit trail is maintained with reference numbers

### Issues Found and Fixed
1. **User Table Reference**: Fixed references from `users` to `org_users` table
2. **Column Names**: Fixed `id` to `user_id` and `username` to `full_name`
3. **Railway Deployment**: Currently showing Express.js errors - needs investigation

### Next Steps
1. **Fix Railway Deployment**: The production URL is serving Express.js instead of FastAPI
2. **Run Triggers**: Execute `03c_inventory_movement_triggers.sql` in production database
3. **Frontend Integration**: Update frontend to use these endpoints
4. **Monitor**: Check if "out of stock" display issue is resolved

### API Usage Examples

```bash
# Sales Return
curl -X POST "https://your-api-url/api/v1/sales-returns/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 38,
    "product_id": 14,
    "batch_id": 4,
    "quantity": 2,
    "reason": "Damaged packaging"
  }'

# Stock Adjustment (Damage)
curl -X POST "https://your-api-url/api/v1/stock-adjustments/" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": 4,
    "adjustment_type": "damage",
    "quantity_adjusted": -3,
    "reason": "Water damage"
  }'

# Physical Count
curl -X POST "https://your-api-url/api/v1/stock-adjustments/physical-count" \
  -H "Content-Type: application/json" \
  -d '{
    "count_date": "2025-07-19",
    "count_items": [{
      "batch_id": 4,
      "counted_quantity": 790
    }]
  }'

# Tax Calculation
curl -X POST "https://your-api-url/api/v1/tax-entries/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "taxable_amount": 1000,
    "gst_rate": 12,
    "is_interstate": false
  }'
```