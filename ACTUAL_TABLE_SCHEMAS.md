# Actual Database Schema (From Production Data)

## challans table
```sql
CREATE TABLE challans (
    challan_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    challan_number VARCHAR(50) UNIQUE NOT NULL,
    challan_date DATE NOT NULL,
    dispatch_date DATE,
    expected_delivery_date DATE,
    vehicle_number VARCHAR(50),
    driver_name VARCHAR(100),
    driver_phone VARCHAR(15),
    transport_company VARCHAR(200),
    lr_number VARCHAR(50),
    freight_amount DECIMAL(10,2) DEFAULT 0,
    delivery_address TEXT,
    delivery_city VARCHAR(100),
    delivery_state VARCHAR(100),
    delivery_pincode VARCHAR(10),
    delivery_contact_person VARCHAR(100),
    delivery_contact_phone VARCHAR(15),
    status VARCHAR(20) DEFAULT 'draft',
    dispatch_time TIMESTAMP,
    delivery_time TIMESTAMP,
    remarks TEXT,
    special_instructions TEXT,
    total_packages INTEGER,
    total_weight DECIMAL(10,2),
    prepared_by INTEGER,
    dispatched_by INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    converted_to_invoice BOOLEAN DEFAULT FALSE,
    invoice_id INTEGER,
    conversion_date DATE,
    org_id UUID NOT NULL DEFAULT '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
);
```

## challan_items table
```sql
CREATE TABLE challan_items (
    challan_item_id SERIAL PRIMARY KEY,
    challan_id INTEGER NOT NULL REFERENCES challans(challan_id),
    order_item_id INTEGER NOT NULL REFERENCES order_items(order_item_id),
    batch_id INTEGER,
    ordered_quantity INTEGER NOT NULL,
    dispatched_quantity INTEGER NOT NULL,
    pending_quantity INTEGER DEFAULT 0,
    product_name VARCHAR(200),
    batch_number VARCHAR(50),
    expiry_date DATE,
    unit_price DECIMAL(10,2) NOT NULL,
    package_type VARCHAR(50),
    packages_count INTEGER,
    created_at TIMESTAMP,
    product_id INTEGER NOT NULL REFERENCES products(product_id)
);
```

## Key Relationships
1. **Order → Challan**: One order can have multiple challans (partial deliveries)
2. **Order Items → Challan Items**: Each challan_item references an order_item
3. **Challan → Invoice**: A challan can be converted to invoice (converted_to_invoice flag)

## The Problem
The current flow assumes:
- Direct Challan creation (without order) → But challan_items REQUIRES order_item_id
- This creates a conflict when trying to create challans directly

## Solutions
1. **Option A**: Always create an order first (even for direct challans)
2. **Option B**: Make order_item_id nullable in challan_items
3. **Option C**: Create a different table for direct challans