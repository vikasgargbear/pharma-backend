# AASO Pharma Purchase Order System

## Overview

A comprehensive purchase order management system with intelligent batch tracking, designed specifically for pharmaceutical operations.

## Key Features

### 🎯 Intelligent Batch Management
- **Auto-Generation**: Creates batch numbers when missing (`AUTO-20250120-14-1234`)
- **Smart Defaults**: Sets expiry date (2 years) and manufacturing date (30 days ago)
- **Duplicate Prevention**: Checks before creating to avoid conflicts

### 📄 PDF Invoice Processing
- Extract supplier information
- Parse product details and quantities
- Handle incomplete data gracefully

### 📦 Inventory Integration
- Automatic stock updates via database triggers
- FEFO (First Expiry First Out) tracking
- Real-time inventory movements

### 💰 Financial Tracking
- Supplier outstanding management
- GST calculations
- Payment tracking

## Quick Start

### 1. Create Purchase Order
```bash
POST /api/v1/purchases-enhanced/with-items
{
  "supplier_id": 1,
  "items": [{
    "product_id": 14,
    "quantity": 100
    # Batch info optional
  }]
}
```

### 2. Receive Goods
```bash
POST /api/v1/purchases-enhanced/{id}/receive-fixed
{
  "items": [{
    "purchase_item_id": 1,
    "received_quantity": 100
    # Batch auto-generated if not provided
  }]
}
```

### 3. Parse PDF Invoice
```bash
POST /api/v1/purchase-upload/parse-invoice
Content-Type: multipart/form-data
file: invoice.pdf
```

## System Architecture

```
Frontend → FastAPI Backend → PostgreSQL (Supabase)
                ↓                    ↓
           Bill Parser         Database Triggers
           (PDF/OCR)          (Auto Batch Creation)
```

## Documentation

- **[Enterprise Documentation](docs/ENTERPRISE_PURCHASE_SYSTEM.md)** - Complete system guide
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - How to deploy
- **[API Reference](https://pharma-backend-production-0c09.up.railway.app/docs)** - Interactive API docs

## Testing

```bash
# Run complete test suite
python tests/test_purchase_system.py

# Test specific scenarios
python test_auto_batch_fixed.py
python test_complete_scenarios.py
```

## Database Migration

The system requires one migration to be run:
```sql
-- database/migrations/V004__purchase_system_enhancements.sql
```

## Key Improvements Made

1. **Trigger Consolidation**: All SQL fixes merged into single migration
2. **Batch Generation**: Handles null batch numbers automatically
3. **API Enhancement**: New `/receive-fixed` endpoint avoids conflicts
4. **Documentation**: Enterprise-ready documentation structure
5. **Test Suite**: Comprehensive testing scenarios

## Support

- **Issues**: Create GitHub issue
- **Documentation**: See `/docs` directory
- **API Docs**: Visit `/docs` endpoint

---

*Built for AASO Pharma - Enterprise Pharmaceutical ERP*