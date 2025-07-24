# Backend API Update for New Pack Fields

## Summary
The backend API has been updated to support the new pack configuration fields added in the database migration.

## Changes Made

### 1. SQLAlchemy Models (`api/models.py`)
Added new pack configuration columns to the Product model:
- `pack_input` - Raw user input like '10*10' or '1*100ML'
- `pack_quantity` - Quantity per unit (first number)
- `pack_multiplier` - Multiplier or units per box (second number)
- `pack_unit_type` - Unit type like ML, GM, MG
- `unit_count` - Units per package
- `unit_measurement` - Measurement with unit like '100ML'
- `packages_per_box` - Packages per box

### 2. Pydantic Schemas (`api/schemas_v2/product_schema.py`)
Created new schema models:
- `ProductPackConfig` - Embedded model for pack configuration
- `ProductCreate` - Request model with pack fields and validation
- `ProductUpdate` - Update model with optional pack fields
- `ProductResponse` - Response model with pack_config embedded object

### 3. API Routes (`api/routers/products.py`)
Updated endpoints to use new schemas:
- `POST /products` - Creates product with pack fields, handles initial batch creation
- `GET /products` - Returns pack_config in response
- `GET /products/{id}` - Returns full product with pack_config
- `PUT /products/{id}` - Updates product pack fields

### 4. Base Schemas (`api/base_schemas.py`)
Extended base schemas to include:
- New pack fields in ProductBase
- Additional fields in ProductCreate (quantity_received, expiry_date, cost_price)
- Pack configuration in ProductResponse

## API Usage Example

### Create Product Request
```json
{
  "product_name": "Paracetamol 500mg",
  "manufacturer": "ABC Pharma",
  "hsn_code": "30049099",
  "category": "Tablet",
  "salt_composition": "Paracetamol 500mg",
  "mrp": 100.00,
  "sale_price": 90.00,
  "cost_price": 70.00,
  "gst_percent": 12,
  "base_unit": "Tablet",
  "sale_unit": "Strip",
  "quantity_received": 100,
  "expiry_date": "2025-12-01",
  
  "pack_input": "10*10",
  "pack_quantity": 10,
  "pack_multiplier": 10,
  "packages_per_box": 10
}
```

### Response
```json
{
  "product_id": 1,
  "product_code": "PRD123456",
  "product_name": "Paracetamol 500mg",
  "manufacturer": "ABC Pharma",
  "hsn_code": "30049099",
  "category": "Tablet",
  "salt_composition": "Paracetamol 500mg",
  "mrp": 100.00,
  "sale_price": 90.00,
  "cost_price": 70.00,
  "gst_percent": 12,
  "base_unit": "Tablet",
  "sale_unit": "Strip",
  "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
  "is_active": true,
  "created_at": "2024-01-23T23:30:00",
  "updated_at": "2024-01-23T23:30:00",
  "pack_config": {
    "pack_input": "10*10",
    "pack_quantity": 10,
    "pack_multiplier": 10,
    "pack_unit_type": null,
    "unit_count": 10,
    "unit_measurement": null,
    "packages_per_box": 10
  }
}
```

## Backward Compatibility
- The API maintains backward compatibility with existing pack_type, pack_size fields
- The frontend sends both new and legacy fields during transition
- Legacy fields will be removed once all systems are updated

## Testing
Run the test script to validate schemas:
```bash
python test_product_api.py
```

## Notes
- Initial batch creation is automatic if quantity_received and expiry_date are provided
- Pack configuration is validated and auto-generated pack_input if components are provided
- All numeric fields are properly typed (Decimal for prices, int for quantities)