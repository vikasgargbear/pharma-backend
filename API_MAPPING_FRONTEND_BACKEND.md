# Frontend-Backend API Mapping Document

## Overview
This document maps the frontend API expectations to the current backend API structure, identifying mismatches and required adaptations.

## Authentication APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `POST /api/v1/auth/login` | `POST /api/v1/auth/login` | ✅ Match | None |
| `POST /api/v1/auth/logout` | `POST /api/v1/auth/logout` | ✅ Match | None |
| `POST /api/v1/auth/refresh` | `POST /api/v1/auth/refresh` | ✅ Match | None |
| `GET /api/v1/auth/verify` | `GET /api/v1/auth/verify` | ✅ Match | None |

## Customer APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/customers` | `GET /api/v1/customers` | ✅ Match | Field mapping needed |
| `GET /api/v1/customers/search` | `GET /api/v1/customers/search` | ✅ Match | None |
| `GET /api/v1/customers/credit-check` | Not found | ❌ Missing | Create endpoint |
| Field: `outstanding_balance` | Field: `current_outstanding` | ⚠️ Mismatch | Map in response |

## Product APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/products` | `GET /api/v1/products` | ✅ Match | None |
| `GET /api/v1/products/search` | `GET /api/v1/products/search` | ✅ Match | None |
| `POST /api/v1/products/batch-upload` | Not found | ❌ Missing | Create endpoint |
| `GET /api/v1/products/categories` | Check master schema | ❓ Check | Verify endpoint |

## Sales APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `POST /api/v1/sales/direct-invoice-sale` | `POST /api/v1/direct-invoice` | ⚠️ Different | Create alias |
| `GET /api/v1/sales/invoices/search` | `GET /api/v1/invoices/search` | ⚠️ Different | Create alias |
| `GET /api/v1/orders` (with challan type) | `GET /api/v1/enterprise-orders` | ⚠️ Different | Map order_type |
| `POST /api/v1/invoices/calculate-live` | Check invoice router | ❓ Check | Verify endpoint |

## Purchase APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/purchases` | `GET /api/v1/purchases` | ✅ Match | None |
| `GET /api/v1/purchases-enhanced` | `GET /api/v1/purchase-enhanced` | ⚠️ Different | Create alias |
| `POST /api/v1/purchase-upload/parse-invoice-safe` | `POST /api/v1/purchase-upload/parse-invoice` | ⚠️ Different | Create alias |

## Inventory APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/batches` | Check inventory router | ❓ Check | Verify endpoint |
| `GET /api/v1/inventory-movements` | `GET /api/v1/stock-movements` | ⚠️ Different | Create alias |
| `GET /api/v1/inventory/stock-levels` | Check inventory router | ❓ Check | Create if missing |

## Payment APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/payments` | `GET /api/v1/payments` | ✅ Match | None |
| `POST /api/v1/payments/reconcile` | Check payment router | ❓ Check | Verify endpoint |

## GST & Reports APIs
| Frontend Expects | Backend Provides | Status | Action Required |
|-----------------|------------------|---------|-----------------|
| `GET /api/v1/reports/gst/gstr1` | Not implemented | ❌ Missing | Create endpoint |
| `GET /api/v1/reports/gst/gstr3b` | Not implemented | ❌ Missing | Create endpoint |
| `GET /api/v1/dashboard` | `GET /api/v1/dashboard` | ✅ Match | None |

## Field Name Mappings
| Frontend Field | Backend Field | Table | Notes |
|---------------|---------------|--------|--------|
| `outstanding_balance` | `current_outstanding` | customers | Update in API response |
| `gstin` | `gst_number` | customers/suppliers | Map in both directions |
| `contact_info.primary_phone` | `primary_phone` | customers | Flatten structure |
| `address_info.billing_address` | `billing_address` | customers | Flatten structure |

## Critical Missing Endpoints
1. **Credit Check API**: `/api/v1/customers/credit-check`
2. **Batch Product Upload**: `/api/v1/products/batch-upload`
3. **GST Reports**: `/api/v1/reports/gst/*`
4. **Inventory Stock Levels**: `/api/v1/inventory/stock-levels`
5. **Payment Reconciliation**: `/api/v1/payments/reconcile`

## Quick Fix Strategy
1. Create an Express.js middleware layer to handle translations
2. Add missing endpoints to backend
3. Map field names in API responses
4. Use aliases for differently named endpoints
5. Implement missing business logic

## Implementation Priority
1. **High**: Authentication, Customers, Products (Core data)
2. **High**: Sales/Invoice creation flow
3. **Medium**: Inventory management
4. **Medium**: Purchase workflows
5. **Low**: Reports and analytics (post-MVP)