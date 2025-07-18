# Pharma Backend Data Dictionary

## Overview
This document provides a comprehensive data dictionary for the AASO Pharma Backend database. It's designed to be AI-queryable, allowing you to ask natural language questions about the database structure.

## Quick Reference for AI Queries

### Common Query Patterns:
- "Show me all customer related fields" → Look at customers table
- "What fields track money/amounts?" → Search for DECIMAL fields with 'amount', 'price', 'cost'
- "Find all date fields" → Search for DATE/TIMESTAMP columns
- "What links customers to orders?" → customer_id foreign key
- "Show GST related fields" → Search for 'gst', 'cgst', 'sgst', 'igst'

## Database Tables Summary

| Table | Purpose | Row Count Estimate |
|-------|---------|-------------------|
| organizations | Multi-tenant organizations | Low (1-100) |
| org_users | User accounts per organization | Medium (10-1000) |
| org_branches | Branch locations | Low (1-50) |
| products | Product master catalog | High (1000-50000) |
| customers | Customer master | High (100-10000) |
| suppliers | Supplier master | Medium (10-500) |
| batches | Inventory batch tracking | Very High (10000+) |
| orders | Sales orders | Very High (1000+ per month) |
| order_items | Order line items | Very High (5x orders) |
| invoices | Tax invoices | Very High (matches orders) |
| invoice_items | Invoice line items | Very High (5x invoices) |
| doctors | Doctor master for prescriptions | Medium (10-1000) |
| prescriptions | Prescription tracking | High (varies) |

## Detailed Table Definitions

### 1. CUSTOMERS Table Analysis

**Purpose**: Master record of all customers (pharmacies, hospitals, clinics, retail)

**Key Fields**:
```
IDENTITY:
- customer_id (PK)
- customer_code (unique identifier like CUST001)
- customer_name* (business name)
- customer_type (retail/wholesale/hospital/clinic/pharmacy)

CONTACT:
- phone* (primary - 10 digits)
- alternate_phone
- email
- contact_person (added later for B2B)

ADDRESS:
- address / address_line1* (street address)
- address_line2
- area (locality - added via migration)
- city*
- state*
- pincode* (6 digits)
- landmark (REDUNDANT with area)

BUSINESS/TAX:
- business_type (REDUNDANT with customer_type)
- gst_number / gstin (GST registration)
- pan_number
- drug_license_number
- food_license_number

CREDIT/FINANCIAL:
- credit_limit (max credit allowed)
- credit_period_days / credit_days (payment terms)
- payment_terms (text description)
- outstanding_amount (current dues)
- total_business (lifetime value)

SALES MANAGEMENT:
- assigned_sales_rep (user_id reference)
- customer_group / customer_category (grouping)
- price_list_id (special pricing)
- discount_percent (default discount)

ACTIVITY TRACKING:
- last_order_date
- order_count
- loyalty_points

OPERATIONAL:
- preferred_payment_mode
- collection_route
- visiting_days (array of weekdays)
- monthly_potential (business potential)

STATUS:
- is_active
- blacklisted
- blacklist_reason

METADATA:
- created_by (user_id)
- created_at
- updated_at
- notes
```

**Redundancies Found**:
1. **landmark** vs **area** - Both store locality info
2. **business_type** vs **customer_type** - Duplicate categorization
3. **credit_period_days** vs **credit_days** - Same field different names
4. **gst_number** vs **gstin** - Same field different names
5. **address** vs **address_line1** - Migration issue

**Recommendations**:
- Remove: landmark, business_type, credit_period_days, gst_number, address
- Keep: area, customer_type, credit_days, gstin, address_line1

### 2. PRODUCTS Table

**Key Fields**:
```
IDENTITY:
- product_id (PK)
- product_code* (SKU)
- product_name*
- generic_name
- brand_name
- manufacturer

CATEGORIZATION:
- category / category_id
- subcategory
- product_type_id
- therapeutic_category

UNITS:
- base_uom_code (smallest unit)
- purchase_uom_code
- sale_uom_code
- pack_size

PRICING:
- purchase_price
- sale_price
- mrp (maximum retail)
- trade_discount_percent

TAX:
- hsn_code
- gst_percent (total GST)
- cgst_percent
- sgst_percent
- igst_percent

REGULATORY:
- drug_schedule
- prescription_required
- is_controlled_substance
- is_narcotic
- is_habit_forming

INVENTORY:
- minimum_stock_level
- reorder_level
- reorder_quantity

STORAGE:
- storage_location
- shelf_life_days
- requires_cold_chain
- temperature_range
```

### 3. ORDERS Table

**Key Fields**:
```
IDENTITY:
- order_id (PK)
- order_number* (unique)
- order_date*
- customer_id* (FK)

AMOUNTS:
- subtotal_amount
- discount_amount
- tax_amount
- final_amount
- paid_amount
- balance_amount

PAYMENT:
- payment_mode
- payment_status
- payment_due_date

DELIVERY:
- delivery_type
- delivery_address
- delivery_status
- delivered_date

STATUS:
- order_status (pending/confirmed/packed/shipped/delivered/cancelled)
```

### 4. INVOICES Table

**Key Fields**:
```
IDENTITY:
- invoice_id (PK)
- invoice_number (INV-YYYY-MM-00001)
- invoice_date
- order_id (FK)
- customer_id (FK)

FINANCIAL:
- subtotal_amount
- discount_amount
- tax_amount
- total_amount
- paid_amount
- balance_amount

TAX BREAKDOWN:
- cgst_amount
- sgst_amount
- igst_amount

STATUS:
- payment_status
- due_date

STORAGE:
- pdf_url
- pdf_generated_at
```

## AI Query Examples

### Find all money-related fields:
```sql
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE data_type = 'numeric' 
  AND column_name LIKE '%amount%' 
   OR column_name LIKE '%price%' 
   OR column_name LIKE '%cost%'
   OR column_name LIKE '%limit%';
```

### Find all date fields:
```sql
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE data_type IN ('date', 'timestamp', 'timestamp with time zone')
ORDER BY table_name, column_name;
```

### Find all GST related fields:
```sql
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name LIKE '%gst%' 
   OR column_name IN ('hsn_code', 'tax_amount', 'tax_percent');
```

### Find customer contact information:
```sql
SELECT customer_name, phone, email, 
       COALESCE(area, landmark) as locality,
       city, state
FROM customers 
WHERE is_active = true;
```

## Storage Optimization Recommendations

### High Impact Changes:
1. **Remove duplicate columns** in customers table (save ~20% space)
2. **Use ENUM types** instead of TEXT for status fields
3. **Normalize** denormalized data (customer_name in orders)
4. **Archive** old orders/invoices (>2 years)

### Estimated Storage Savings:
- Removing redundant columns: ~50-100 bytes per customer row
- Using ENUMs: ~10-20 bytes per status field
- With 10,000 customers: ~1-2 MB saved
- With 100,000 orders: ~5-10 MB saved

## Quick Stats Queries

### Table sizes:
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Row counts:
```sql
SELECT 
    'customers' as table_name, COUNT(*) as row_count FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices;
```

## How to Use This Document

1. **For AI Queries**: Ask questions like:
   - "What fields store customer addresses?"
   - "Show me all financial fields in orders"
   - "Which tables have GST information?"

2. **For Development**: 
   - Check field names before queries
   - Understand relationships
   - Avoid using redundant fields

3. **For Analysis**:
   - Use the query examples
   - Check storage recommendations
   - Monitor table growth

This document is your single source of truth for database structure!