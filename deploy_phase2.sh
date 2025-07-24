#!/bin/bash
# Deploy Phase 2 Backend Updates

echo "🚀 Deploying Phase 2 Backend Updates..."
echo "======================================="

# Check git status
echo "📋 Checking git status..."
git status

# Add all changes
echo "📝 Adding all changes..."
git add -A

# Commit with detailed message
echo "💾 Committing changes..."
git commit -m "feat: Complete Phase 2 ERP backend implementation

- Added modular GST service following industry standards (Marg/Vyapar patterns)
- Implemented CGST/SGST for intra-state and IGST for inter-state transactions
- Created comprehensive Phase 2 APIs:
  * Sale Returns with inventory reversal and credit notes
  * Purchase Returns with debit note generation
  * Manual Stock Movements (receive/issue)
  * Party Ledger with ageing analysis
  * Credit/Debit Notes for adjustments
  * Direct Sales endpoint with GST calculation
- Fixed invoice creation validation errors (unit_price, tax_percent)
- All APIs follow RESTful patterns with proper error handling
- Database triggers handle automatic ledger updates

API Endpoints:
- POST /api/v1/sales - Create direct sale/invoice
- /api/v1/sale-returns - Sale return management
- /api/v1/purchase-returns - Purchase return management
- /api/v1/stock-movements - Manual stock operations
- /api/v1/party-ledger - Customer/supplier ledger
- /api/v1/credit-debit-notes - Financial adjustments"

# Push to remote
echo "🌐 Pushing to remote repository..."
git push origin main

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Check Railway deployment status"
echo "2. Test the new endpoints using test_gst_sales.py"
echo "3. Update frontend to use /api/v1/sales for invoice creation"
echo "4. Frontend should send unit_price and tax_percent for each item"