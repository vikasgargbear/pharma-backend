# Purchase Order Upload & Management Guide

## Overview

The AASO Pharma ERP now supports both automated PDF/image upload for purchase orders and manual entry with line items. This feature uses AI-powered extraction specifically tuned for pharmaceutical invoices.

## Key Features

### 1. **PDF/Image Upload with Auto-Extraction**
- Upload supplier invoices in PDF or image format
- Automatic extraction of:
  - Supplier details (name, GSTIN, address)
  - Invoice metadata (number, date, amounts)
  - Line items with pharmaceutical details
  - Batch numbers and expiry dates
  - HSN codes and tax information

### 2. **Intelligent Matching**
- Auto-match suppliers by GSTIN
- Product matching by name and HSN code
- Duplicate invoice detection
- Confidence scoring for extraction accuracy

### 3. **Manual Entry Support**
- Full manual purchase order creation
- Line-by-line item entry
- Batch and expiry tracking
- Multi-UOM support

### 4. **Goods Receipt & Inventory Update**
- Receive items against purchase orders
- Auto-create batches with FEFO tracking
- Update inventory movements
- Generate GRN (Goods Receipt Note)

## API Endpoints

### Upload & Parse Invoice
```http
POST /api/v1/purchase-upload/parse-invoice
Content-Type: multipart/form-data

file: [PDF or image file]
```

**Response:**
```json
{
  "status": "success",
  "confidence_score": 0.95,
  "extracted_data": {
    "invoice_number": "INV/2024/12345",
    "invoice_date": "2024-01-15",
    "supplier_name": "ABC Pharma Distributors",
    "supplier_gstin": "27AABCA1234B1Z5",
    "supplier_matched": true,
    "supplier_id": 123,
    "subtotal": 10000.00,
    "tax_amount": 1200.00,
    "grand_total": 11200.00,
    "items": [
      {
        "description": "Paracetamol 500mg",
        "hsn_code": "3004",
        "batch_number": "PCT2024A",
        "expiry_date": "2026-12-31",
        "quantity": 100,
        "rate": 50.00,
        "mrp": 75.00,
        "tax_percent": 12.0,
        "product_matched": true,
        "product_id": 45
      }
    ]
  },
  "manual_review_required": false
}
```

### Validate Invoice Data
```http
POST /api/v1/purchase-upload/validate-invoice
Content-Type: application/json

{
  "invoice_number": "INV/2024/12345",
  "supplier_id": 123,
  "items": [...]
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "Item 2: Product not matched and not marked for creation"
  ]
}
```

### Create Purchase from Parsed Data
```http
POST /api/v1/purchase-upload/create-from-parsed
Content-Type: application/json

{
  "supplier_id": 123,
  "invoice_number": "INV/2024/12345",
  "invoice_date": "2024-01-15",
  "subtotal": 10000.00,
  "tax_amount": 1200.00,
  "grand_total": 11200.00,
  "items": [
    {
      "product_id": 45,
      "description": "Paracetamol 500mg",
      "quantity": 100,
      "rate": 50.00,
      "batch_number": "PCT2024A",
      "expiry_date": "2026-12-31"
    }
  ]
}
```

### Manual Purchase with Items
```http
POST /api/v1/purchases-enhanced/with-items
Content-Type: application/json

{
  "supplier_id": 123,
  "purchase_date": "2024-01-15",
  "supplier_invoice_number": "INV-12345",
  "subtotal_amount": 1000.00,
  "tax_amount": 120.00,
  "final_amount": 1120.00,
  "items": [
    {
      "product_id": 14,
      "ordered_quantity": 50,
      "cost_price": 20.00,
      "mrp": 30.00,
      "tax_percent": 12.0,
      "batch_number": "BATCH-2024",
      "expiry_date": "2026-01-01"
    }
  ]
}
```

### Receive Purchase Items
```http
POST /api/v1/purchases-enhanced/{purchase_id}/receive
Content-Type: application/json

{
  "items": [
    {
      "purchase_item_id": 1,
      "received_quantity": 50,
      "batch_number": "BATCH-2024",
      "expiry_date": "2026-01-01"
    }
  ]
}
```

## Workflow

### Automated Upload Flow
```
1. Upload Invoice PDF/Image
   ↓
2. AI Extraction & Parsing
   ↓
3. Review & Edit Extracted Data
   ↓
4. Validate Invoice
   ↓
5. Create Purchase Order
   ↓
6. Receive Goods (GRN)
   ↓
7. Auto-update Inventory
```

### Manual Entry Flow
```
1. Create Purchase Order Header
   ↓
2. Add Line Items
   ↓
3. Save as Draft
   ↓
4. Approve Purchase
   ↓
5. Receive Goods
   ↓
6. Update Inventory
```

## Implementation Details

### Bill Parser Features
- **Multi-engine PDF extraction**: Uses pdfplumber, PyMuPDF, and pdfminer
- **OCR fallback**: For scanned documents using Tesseract
- **Table extraction**: Specialized algorithms for invoice tables
- **Pharma patterns**: 50+ regex patterns for Indian pharmaceutical companies
- **Confidence scoring**: Each extraction has a confidence score

### Database Schema

#### purchases table
- Standard purchase order header information
- Links to suppliers
- Tracks invoice details and payment status

#### purchase_items table
- Line-level details for each product
- Batch and expiry tracking
- Quantity tracking (ordered vs received)
- Pricing and tax details

#### Automatic Updates
- Creates batches on goods receipt
- Updates inventory_movements
- Maintains FEFO (First Expiry First Out)
- Updates supplier outstanding

## Best Practices

### For Upload
1. **Use clear, readable invoices** - Better quality = higher accuracy
2. **Standard formats work best** - The parser is trained on common pharma invoice formats
3. **Review extracted data** - Always verify critical fields like amounts and expiry dates

### For Manual Entry
1. **Use product codes** - Faster than searching by name
2. **Verify batch numbers** - Critical for pharmaceutical compliance
3. **Check expiry dates** - System will alert for short-dated items

### For Receiving
1. **Match physical batches** - Ensure batch numbers match invoice
2. **Inspect for damage** - Record damaged quantities
3. **Update immediately** - Real-time inventory accuracy

## Error Handling

### Common Issues
1. **Low confidence extraction**
   - Solution: Use manual entry or edit extracted data
   
2. **Duplicate invoice**
   - Solution: System prevents duplicates, check if already entered
   
3. **Product not found**
   - Solution: Create product during purchase or maintain product master

4. **Expired items**
   - Solution: System blocks expired items, return to supplier

## Security & Compliance

- **File handling**: Temporary files are deleted after processing
- **Data validation**: All inputs are validated
- **Audit trail**: All changes are logged
- **GST compliance**: Automatic tax calculations
- **Drug license**: Validation for controlled substances

## Frontend Integration

### Upload Component
```javascript
const uploadInvoice = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/v1/purchase-upload/parse-invoice', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  // Display extracted data for review
};
```

### Review & Edit UI
- Show confidence scores with color coding
- Highlight unmatched items
- Allow inline editing
- Show validation errors/warnings

### Quick Actions
- One-click supplier creation
- Bulk product matching
- Auto-calculate totals
- Quick receive for full orders

## Performance Tips

1. **Batch uploads**: Process multiple invoices in sequence
2. **Pre-match products**: Maintain clean product master
3. **Regular supplier updates**: Keep GSTIN updated
4. **Use shortcuts**: Keyboard navigation for faster entry

## Future Enhancements

1. **Email integration**: Auto-fetch invoices from email
2. **Supplier portals**: Direct API integration
3. **Mobile app**: Scan and upload on the go
4. **AI improvements**: Learn from corrections
5. **Automated approvals**: Rule-based auto-approval

## Support

For issues with:
- **Extraction accuracy**: Provide sample invoices for training
- **Integration**: Check API documentation
- **Performance**: Review upload file sizes
- **Compliance**: Ensure all regulatory fields are mapped