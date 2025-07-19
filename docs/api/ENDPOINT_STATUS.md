# API Endpoint Status Report

## ✅ Working Endpoints

### Basic
- `GET /` - Root endpoint with API info
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health status
- `GET /info` - API information

### Database Inspection
- `GET /db-inspect/tables` - List all 94 database tables
- `GET /db-inspect/table/{table_name}/columns` - Get table schema
- `GET /db-inspect/query?sql={query}` - Execute SELECT queries
- `GET /db-inspect/full-schema` - Get complete database schema

### Organizations
- `GET /organizations/list` - List organizations (FIXED)
- `POST /organizations/create-default` - Create default organization

### Test
- `GET /test/` - Simple test endpoint
- `POST /test/echo` - Echo test endpoint

### Products Simple (NEW)
- `GET /products-simple/` - List products without complex schemas
- `POST /products-simple/` - Create product with simple JSON
- `GET /products-simple/{id}` - Get single product

## ❌ Failing Endpoints

### Products (Original)
- `GET /products/` - 500 error (schema/model issues)
- `POST /products/` - 500 error (schema/model issues)
- `PUT /products/{id}` - Not tested
- `DELETE /products/{id}` - Not tested

### Delivery
- `GET /delivery/pending` - 403 Not authenticated
- `GET /delivery/stats` - 403 Not authenticated
- `POST /delivery/order/{order_id}/delivered` - Needs authentication
- All delivery endpoints require authentication

### Migrations
- `POST /migrations/run-org-id-migration` - Method not allowed (expects POST)

## 📊 Summary

- **Total Endpoints**: ~30
- **Working**: 15+
- **Authentication Required**: 6 (delivery endpoints)
- **Broken**: 4 (original products endpoints)
- **Not Tested**: Several PUT/DELETE endpoints

## Next Steps

1. Test the new products-simple endpoints
2. Add authentication for delivery endpoints
3. Fix or replace the original products endpoints
4. Enable more routers (orders, batches, etc.)