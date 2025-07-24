# URGENT: Frontend Deployment Guide - Fix "Order X Not Found" Error

**Date**: 2025-07-24  
**Priority**: CRITICAL  
**Issue**: Frontend creating non-existent order IDs (46, 47, 48, 50, 51...) causing "Order not found" errors

## 1. Summary of Changes

The frontend was creating orders first, then trying to generate invoices for those orders. This two-step process was failing because:
- Frontend was incrementing order IDs locally
- Backend sequences weren't matching frontend's assumed IDs
- Result: "Order 46/47/48/50/51 not found" errors

**Solution**: Updated frontend to use the new `/api/v1/quick-sale/` endpoint that creates both order and invoice atomically in one transaction.

## 2. Modified Files

### Critical Frontend Files to Deploy:

1. **src/components/invoice/ModularInvoiceCreatorV2.js**
   - Changed from: `ordersApi.create()` then `generateInvoice()`
   - Changed to: `api.post('/api/v1/quick-sale/')`

2. **src/components/SalesEntryModalV2.js**
   - Changed from: Creating order first, then invoice
   - Changed to: Single quick-sale API call

3. **src/services/invoiceService.js**
   - Added: `createQuickSale()` method
   - Marked `generateInvoiceForOrder()` as deprecated

### Key Changes Example:
```javascript
// BEFORE (Two-step process)
const orderResponse = await ordersApi.create(orderData);
const invoiceResponse = await ordersApi.generateInvoice(orderResponse.data.order_id);

// AFTER (Single atomic transaction)
const response = await api.post('/api/v1/quick-sale/', {
  customer_id: transformedData.customer_id,
  items: transformedData.items,
  payment_mode: 'Cash',
  payment_amount: 0
});
```

## 3. Deployment Steps

### Pre-Deployment
- [ ] Ensure backend with `/api/v1/quick-sale/` endpoint is live
- [ ] Take backup of current frontend
- [ ] Alert team about deployment

### Build & Deploy

1. **Navigate to Frontend Directory**
   ```bash
   cd /Users/vikasgarg/Documents/AASO/Infrastructure/pharma-frontend
   ```

2. **Install Dependencies & Build**
   ```bash
   npm install
   npm run build
   ```

3. **Deploy Based on Your Platform**

   **For Local Testing First:**
   ```bash
   npm start
   # Test creating new invoices locally
   ```

   **For Production:**
   ```bash
   # If using npm scripts
   npm run deploy

   # If manual deployment
   # Copy build files to production server
   ```

## 4. Verification Steps

### Immediate Testing After Deployment

1. **Create a New Invoice**
   - Open invoice creation form
   - Add customer and items
   - Click "Save Invoice" or "Create Invoice"
   - **SUCCESS**: Invoice saves without "Order X not found" error

2. **Check Browser Console**
   - Open DevTools Network tab
   - Create an invoice
   - Look for: `POST /api/v1/quick-sale/`
   - **SUCCESS**: Returns 200 with invoice details

3. **Verify Response**
   ```javascript
   // Expected response structure:
   {
     "success": true,
     "invoice_number": "INV202507240001",
     "total_amount": 1000.00,
     "order_id": 52,  // Backend-generated ID
     "invoice_id": 1
   }
   ```

### What to Look For:
- ✅ No more "Order not found" errors
- ✅ Invoice saves successfully
- ✅ Frontend uses `/api/v1/quick-sale/` endpoint
- ✅ All tax calculations work (GST is taken from product master)

## 5. Rollback Plan

If issues occur:

1. **Immediate Rollback**
   ```bash
   # Restore previous build
   git checkout HEAD~1 -- src/components/invoice/ModularInvoiceCreatorV2.js
   git checkout HEAD~1 -- src/components/SalesEntryModalV2.js
   git checkout HEAD~1 -- src/services/invoiceService.js
   
   # Rebuild and deploy
   npm run build
   npm run deploy
   ```

2. **Temporary Workaround**
   - Users can use direct invoice creation if available
   - Or manually create orders first, then invoices

## 6. Important Notes

### Tax Data Handling
The backend properly handles all tax data:
- GST percentage is fetched from product master
- CGST/SGST are calculated automatically
- No need to send tax data from frontend

### What This Fixes
- ✅ Eliminates "Order 46/47/48/50/51 not found" errors
- ✅ Creates order and invoice in single transaction
- ✅ No more order ID mismatches
- ✅ Proper inventory updates
- ✅ Correct tax calculations

### What This Doesn't Change
- Existing orders/invoices remain unchanged
- Order history still works
- All other features unchanged

## 7. Post-Deployment Monitoring

Monitor for 1 hour after deployment:
- Check error logs for any "Order not found" messages
- Verify new invoices are being created
- Ensure inventory is updating correctly
- Watch for any user complaints

## 8. Success Criteria

Deployment is successful when:
- Zero "Order X not found" errors
- All new invoices save successfully
- Users can complete sales workflow
- No regression in other features

---

**DEPLOY ASAP** - Users are unable to create invoices until this is deployed!