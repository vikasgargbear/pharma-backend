#!/bin/bash
# Deploy GST fixes and sales API updates

echo "🚀 Deploying GST Fixes and Sales API Updates..."
echo "============================================="

# Check git status
echo "📋 Checking git status..."
git status

# Add all changes
echo "📝 Adding all changes..."
git add -A

# Commit with detailed message
echo "💾 Committing changes..."
git commit -m "fix: Update sales API to use existing invoices table with GST support

- Fixed sales API to use existing invoices table instead of non-existent sales table
- Invoices table already has all GST columns (cgst_amount, sgst_amount, igst_amount)
- Sales API now properly creates invoices with GST breakup
- Frontend updated to use direct sales API (/api/v1/sales)
- Added GST calculation based on seller and buyer state codes
- Company settings utility added for managing company GSTIN

Frontend Changes:
- CompleteInvoiceCreator now uses salesApi.create() instead of ordersApi
- Automatic CGST/SGST vs IGST determination based on state codes
- Fixed validation errors for unit_price and tax_percent fields
- Company GSTIN stored in localStorage

Backend Changes:
- Sales API creates records in invoices table (not sales table)
- Invoice items created with proper GST breakup
- Cash payments automatically recorded
- Credit sales create party ledger entries

This fixes the issue where CGST/SGST values were not showing in the invoice summary."

# Push to remote
echo "🌐 Pushing to remote repository..."
git push origin main

echo "✅ Deployment complete!"
echo ""
echo "📝 Important Notes:"
echo "1. The invoices table already exists with GST support - no migration needed"
echo "2. Frontend will now properly show CGST/SGST based on customer state"
echo "3. Make sure to set company GSTIN in frontend settings"
echo "4. Direct sales create invoices without orders"