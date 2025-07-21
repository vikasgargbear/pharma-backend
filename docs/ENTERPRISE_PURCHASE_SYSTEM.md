# Enterprise Purchase Order System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [API Reference](#api-reference)
5. [Database Design](#database-design)
6. [Business Logic](#business-logic)
7. [Deployment Guide](#deployment-guide)
8. [Testing Guide](#testing-guide)
9. [Troubleshooting](#troubleshooting)

## System Overview

The AASO Pharma Purchase Order System is a comprehensive solution for managing pharmaceutical procurement, featuring intelligent batch tracking, automated inventory management, and PDF invoice parsing capabilities.

### Core Capabilities
- **Purchase Order Management**: Create, track, and receive purchase orders
- **Intelligent Batch Handling**: Auto-generates batch numbers when missing
- **PDF Invoice Parsing**: Extract data from supplier invoices automatically
- **Inventory Integration**: Automatic stock updates via database triggers
- **Compliance Ready**: FEFO tracking, expiry management, GST calculations

## Architecture

### System Components
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI        │────▶│   PostgreSQL    │
│   (React)       │     │   Backend        │     │   (Supabase)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐          ┌──────────────┐
                        │ Bill Parser  │          │  Triggers    │
                        │ (PDF/OCR)    │          │  Functions   │
                        └──────────────┘          └──────────────┘
```

### Key Design Decisions
1. **Trigger-Based Batch Creation**: Database triggers handle batch creation to ensure consistency
2. **Automatic Defaults**: System provides sensible defaults for missing data
3. **Idempotent Operations**: Duplicate prevention built into all critical operations

## Key Features

### 1. Intelligent Batch Management

#### Auto-Generation Logic
When batch information is missing, the system generates:
- **Format**: `AUTO-YYYYMMDD-PRODUCTID-XXXX`
- **Example**: `AUTO-20250120-14-7523`

#### Default Values
- **Manufacturing Date**: 30 days before current date
- **Expiry Date**: 2 years from current date

### 2. Purchase Receipt Workflow

```mermaid
graph LR
    A[Create Purchase] --> B[Receive Goods]
    B --> C{Batch Info?}
    C -->|Yes| D[Use Provided]
    C -->|No| E[Auto-Generate]
    D --> F[Create Batch]
    E --> F
    F --> G[Update Inventory]
    G --> H[Track Outstanding]
```

### 3. PDF Invoice Processing

The system can extract:
- Supplier information
- Invoice number and date
- Product details with quantities
- Batch numbers (when available)
- Tax calculations

## API Reference

### Purchase Management Endpoints

#### Create Purchase with Items
```http
POST /api/v1/purchases-enhanced/with-items
Content-Type: application/json

{
  "supplier_id": 1,
  "supplier_invoice_number": "INV-2024-001",
  "supplier_invoice_date": "2024-01-20",
  "subtotal_amount": 5000.00,
  "tax_amount": 600.00,
  "final_amount": 5600.00,
  "items": [
    {
      "product_id": 14,
      "ordered_quantity": 100,
      "cost_price": 50.00,
      "batch_number": "BATCH-001",  // Optional
      "expiry_date": "2026-01-20"   // Optional
    }
  ]
}
```

#### Receive Goods (Recommended)
```http
POST /api/v1/purchases-enhanced/{purchase_id}/receive-fixed
Content-Type: application/json

{
  "items": [
    {
      "purchase_item_id": 1,
      "received_quantity": 100,
      "batch_number": "CUSTOM-BATCH",  // Optional - auto-generates if null
      "expiry_date": "2026-01-20"      // Optional - defaults to 2 years
    }
  ]
}
```

#### Parse Invoice PDF
```http
POST /api/v1/purchase-upload/parse-invoice
Content-Type: multipart/form-data

file: invoice.pdf
```

### Response Formats

#### Success Response
```json
{
  "message": "Purchase received successfully",
  "purchase_id": 123,
  "grn_number": "GRN-PO-20250120-1234",
  "batches_created": 1,
  "note": "Batches auto-created with generated numbers if needed"
}
```

## Database Design

### Key Tables

#### purchases
- Stores purchase order header information
- Links to suppliers and organizations
- Tracks status: draft → approved → received

#### purchase_items
- Line items for each purchase
- Can store batch info or leave null for auto-generation
- Tracks ordered vs received quantities

#### batches
- Central batch tracking table
- Unique constraint on (org_id, product_id, batch_number)
- Tracks quantities: received, available, sold, damaged

#### inventory_movements
- Audit trail of all stock movements
- Types: purchase, sales, sales_return, stock_adjustment
- Links to batches and references

### Database Triggers

#### trigger_create_batches_from_purchase
- Fires when purchase_status changes to 'received'
- Auto-generates batch numbers if missing
- Creates inventory movements

#### trigger_validate_inventory_movement
- Validates all inventory transactions
- Special handling for purchase movements
- Ensures data integrity

## Business Logic

### Batch Number Generation Rules

1. **Check Existing**: If batch_number provided, use it
2. **Generate New**: If null, create AUTO-YYYYMMDD-PRODUCTID-XXXX
3. **Prevent Duplicates**: Skip if batch already exists
4. **Set Defaults**: Apply default dates if missing

### Inventory Update Flow

1. Purchase marked as 'received'
2. Trigger creates batches for each item
3. Inventory movements recorded
4. Batch quantities updated
5. Supplier outstanding created

## Deployment Guide

### Prerequisites
- PostgreSQL 12+ (or Supabase)
- Python 3.8+
- FastAPI application server

### Database Migration

1. **Run the consolidated migration**:
```sql
-- Execute in order:
-- V004__purchase_system_enhancements.sql
```

2. **Verify triggers**:
```sql
SELECT proname FROM pg_proc 
WHERE proname IN (
  'validate_inventory_movement',
  'create_batches_from_purchase',
  'create_supplier_outstanding_on_purchase'
);
```

### Application Deployment

1. **Update environment variables**:
```bash
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

2. **Deploy to Railway**:
```bash
railway up
```

3. **Verify endpoints**:
```bash
curl https://your-api.railway.app/health
```

## Testing Guide

### Test Scenarios

#### Scenario 1: No Batch Information
```python
# Create purchase without batch
purchase_data = {
    "items": [{
        "product_id": 14,
        "quantity": 100
        # No batch_number
    }]
}
# Result: AUTO-20250120-14-XXXX generated
```

#### Scenario 2: Custom Batch
```python
# Provide custom batch at receipt
receive_data = {
    "items": [{
        "batch_number": "CUSTOM-001",
        "expiry_date": "2026-12-31"
    }]
}
# Result: Uses provided values
```

#### Scenario 3: PDF Parsing
```python
# Upload PDF with partial data
# System fills missing fields with defaults
```

### Test Scripts
- `test_auto_batch_fixed.py` - Basic auto-generation test
- `test_complete_scenarios.py` - All scenarios test
- `test_final_purchase_flow.py` - End-to-end test

## Troubleshooting

### Common Issues

#### "Batch already exists" Error
- **Cause**: Trying to create duplicate batch
- **Solution**: System now checks before creating

#### "Case not found" Error
- **Cause**: Old trigger version
- **Solution**: Run V004 migration

#### "Null batch_number" Error
- **Cause**: API trying to insert null batch
- **Solution**: Use `/receive-fixed` endpoint

### Health Checks

1. **Check triggers exist**:
```sql
SELECT tgname FROM pg_trigger 
WHERE tgname LIKE '%purchase%';
```

2. **Verify batch generation**:
```sql
SELECT batch_number FROM batches 
WHERE batch_number LIKE 'AUTO-%' 
ORDER BY created_at DESC LIMIT 5;
```

3. **Check inventory movements**:
```sql
SELECT COUNT(*) FROM inventory_movements 
WHERE movement_type = 'purchase';
```

## Best Practices

1. **Always use `/receive-fixed` endpoint** for goods receipt
2. **Let triggers handle batch creation** to avoid conflicts
3. **Provide batch numbers only when specific** requirements exist
4. **Test with real PDFs** before production use
5. **Monitor auto-generated batches** for audit purposes

## Appendix

### Batch Number Formats
- **Manual**: User-defined format
- **Auto**: `AUTO-YYYYMMDD-PRODUCTID-XXXX`
- **PDF**: Extracted from invoice

### Date Defaults
- **Manufacturing**: Current date - 30 days
- **Expiry**: Current date + 2 years

### Status Codes
- **200**: Success
- **400**: Bad request (validation error)
- **404**: Resource not found
- **500**: Server error (check logs)

---

*Version 1.0 - Last Updated: 2025-01-20*