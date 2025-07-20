# Batch Creation Solution

## Overview

The system now supports **automatic batch number generation** when batch numbers are not provided (e.g., missing in PDF parsing or manual entry).

## How It Works

### 1. **Automatic Batch Generation**
When a purchase is marked as received and batch_number is NULL:
- Format: `AUTO-YYYYMMDD-PRODUCTID-RANDOM`
- Example: `AUTO-20250720-14-7523`

### 2. **Default Values**
If not provided, the system sets:
- Manufacturing Date: 30 days before current date
- Expiry Date: 2 years from current date

### 3. **Duplicate Prevention**
- The trigger checks if a batch already exists before creating
- Prevents duplicate batch errors

## Implementation

### Database Trigger
The `create_batches_from_purchase()` function handles:
1. Null batch number → Auto-generates unique batch
2. Existing batch → Skips creation
3. Missing dates → Sets sensible defaults

### API Flow
1. User creates purchase with or without batch numbers
2. During goods receipt, user can override batch info
3. When purchase status → 'received', trigger creates batches
4. Inventory movements are created automatically

## Testing Scenarios

### Scenario 1: PDF with batch info
```json
{
  "items": [{
    "product_id": 14,
    "batch_number": "MFG-2024-001",
    "expiry_date": "2026-12-31"
  }]
}
```
Result: Uses provided batch number

### Scenario 2: PDF without batch info
```json
{
  "items": [{
    "product_id": 14,
    "batch_number": null,
    "expiry_date": null
  }]
}
```
Result: Auto-generates `AUTO-20250720-14-1234`

### Scenario 3: Manual override at receipt
User can provide batch info during goods receipt, which overrides any defaults.

## SQL to Run

```sql
-- Run this in Supabase SQL Editor
-- File: FIX_batch_creation_trigger.sql
```

This ensures batch creation works smoothly whether:
- Parsing PDFs with incomplete data
- Manual entry without batch details
- Goods receipt with custom batch info

## Benefits

1. **No manual batch entry required** - System generates if missing
2. **Consistent format** - AUTO- prefix clearly identifies system-generated batches
3. **Prevents errors** - No null batch_number violations
4. **Flexible** - Can override during goods receipt
5. **Traceable** - Can identify auto-generated vs manual batches