# Frontend Integration Guide - Quick MVP Launch

## Overview
This guide helps you quickly integrate the existing frontend with our new backend structure while maintaining stability.

## 🚀 Quick Start (5-Minute Setup)

### Option 1: Use Compatibility Layer (Recommended for MVP)
The backend now includes a compatibility layer that automatically handles field mappings.

1. **No Frontend Changes Required!**
   - Keep using existing `/api/v1/*` endpoints
   - Backend automatically maps fields like:
     - `outstanding_balance` ↔ `current_outstanding`
     - `gstin` ↔ `gst_number`
     - Nested `contact_info` ↔ Flattened fields

2. **Update Base URL Only**
   ```javascript
   // In pharma-frontend/src/config/api.config.js
   BASE_URL: 'https://your-new-backend-url.com'
   ```

3. **Test Core Flows**
   - Login → Create Customer → Create Invoice → Process Payment

### Option 2: Progressive Migration to v2 APIs
For better performance and new features, gradually migrate to v2 endpoints:

1. **Update API Config**
   ```javascript
   // Add v2 endpoints alongside v1
   ENDPOINTS: {
     // Keep existing v1 endpoints
     CUSTOMERS: {
       BASE: '/customers',
       // Add v2 variants
       BASE_V2: '/api/v2/parties/customers',
     }
   }
   ```

2. **Use New Response Structure**
   ```javascript
   // v2 responses have consistent format
   {
     success: true,
     data: { /* actual data */ },
     meta: { timestamp, version, pagination },
     errors: []
   }
   ```

## 📋 Critical Field Mappings

| Frontend Uses | Backend Provides | Action |
|--------------|------------------|---------|
| `outstanding_balance` | `current_outstanding` | Auto-mapped |
| `gstin` | `gst_number` | Auto-mapped |
| `contact_info.phone` | `primary_phone` | Auto-mapped |
| `address_info.billing_address` | `billing_address` | Auto-mapped |
| Order as Challan | Order with `order_type='challan'` | Use order endpoints |

## 🔧 Backend Endpoints Status

### ✅ Ready to Use
- **Authentication**: `/api/v1/auth/*` - Works as-is
- **Customers**: `/api/v1/customers/*` - Field mapping handled
- **Products**: `/api/v1/products/*` - Direct compatibility
- **Sales**: `/api/v1/sales/*` - Alias mapping active
- **Dashboard**: `/api/v1/dashboard/*` - No changes needed

### ⚠️ Needs Mapping
- **Purchases Enhanced**: Use `/api/v1/purchase-enhanced/*`
- **Inventory Movements**: Maps to `/api/v1/stock-movements/*`
- **Challans**: Use `/api/v1/orders` with `order_type=challan`

### ❌ Not Yet Implemented
- **GST Reports**: `/api/v1/reports/gst/*` - Coming soon
- **Batch Upload**: `/api/v1/products/batch-upload` - In progress

## 🏃 Quick Testing Script

```bash
# Test authentication
curl -X POST https://backend-url/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password","org_code":"ORG001"}'

# Test customer creation (with old field names)
curl -X POST https://backend-url/api/v1/customers \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Pharmacy",
    "customer_type": "pharmacy",
    "contact_info": {
      "primary_phone": "9876543210",
      "email": "test@pharmacy.com"
    },
    "address_info": {
      "billing_address": "123 Main St",
      "billing_city": "Mumbai",
      "billing_state": "Maharashtra",
      "billing_pincode": "400001"
    },
    "gstin": "27ABCDE1234F1Z5",
    "credit_limit": 50000
  }'
```

## 🐛 Common Issues & Solutions

### 1. Field Not Found Errors
**Issue**: Frontend sends `outstanding_balance`, backend expects `current_outstanding`
**Solution**: Already handled by compatibility layer!

### 2. Nested vs Flat Structure
**Issue**: Frontend sends nested `contact_info`, backend stores flat fields
**Solution**: Middleware automatically flattens/nests as needed

### 3. Missing Endpoints
**Issue**: Some v1 endpoints don't exist in new backend
**Solution**: Check alias mappings or use alternative endpoints

### 4. Authentication Context
**Issue**: New backend requires organization context
**Solution**: Include `org_code` in login request

## 📊 Testing Checklist

- [ ] User login with organization code
- [ ] List and search customers
- [ ] Create new customer
- [ ] Check customer credit
- [ ] Create sales order
- [ ] Convert order to invoice
- [ ] Process payment
- [ ] View dashboard

## 🚦 Go-Live Steps

1. **Deploy Backend** with compatibility layer enabled
2. **Update Frontend** base URL only
3. **Test Core Workflows** using existing frontend
4. **Monitor Logs** for any field mapping issues
5. **Progressive Migration** to v2 APIs post-MVP

## 💡 Pro Tips

1. **Keep v1 Endpoints**: Don't remove them during migration
2. **Log Everything**: Enable debug logs to catch mapping issues
3. **Test Incrementally**: One module at a time
4. **Use Feature Flags**: Toggle between v1/v2 endpoints
5. **Monitor Performance**: v2 APIs are faster, migrate hot paths first

## 📞 Support

- Check logs for field mapping: `grep "Field mapped" app.log`
- API Documentation: `/api/v2/docs`
- Health Check: `/api/v2/health`
- Version Info: `/api/v2/version`

---

**Remember**: The goal is to launch MVP quickly. The compatibility layer handles most differences, so you can focus on testing business flows rather than fixing field names!