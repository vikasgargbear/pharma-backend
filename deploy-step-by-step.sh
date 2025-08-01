#!/bin/bash

# Step-by-step deployment with user confirmation

echo "🚀 Enterprise Pharma Backend - Step by Step Deployment"
echo "======================================================"
echo ""

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    echo "Run: export DATABASE_URL='your-connection-string'"
    exit 1
fi

echo "📊 Target database: ${DATABASE_URL:0:50}..."
echo ""

# Ask if user wants to reset
echo "Do you want to reset the database first? (y/n)"
echo "⚠️  WARNING: This will delete ALL data!"
read reset_answer
if [ "$reset_answer" = "y" ]; then
    echo ""
    echo "🗑️  Resetting database..."
    psql $DATABASE_URL << 'EOF'
-- Drop all schemas cascade
DROP SCHEMA IF EXISTS master CASCADE;
DROP SCHEMA IF EXISTS inventory CASCADE;
DROP SCHEMA IF EXISTS parties CASCADE;
DROP SCHEMA IF EXISTS sales CASCADE;
DROP SCHEMA IF EXISTS procurement CASCADE;
DROP SCHEMA IF EXISTS financial CASCADE;
DROP SCHEMA IF EXISTS gst CASCADE;
DROP SCHEMA IF EXISTS compliance CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;
DROP SCHEMA IF EXISTS system_config CASCADE;
DROP SCHEMA IF EXISTS testing CASCADE;
DROP SCHEMA IF EXISTS api CASCADE;
EOF
    echo "✅ Database reset complete"
    echo ""
fi

echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Step 1: Check connection
echo "🔍 Step 1: Testing database connection..."
psql $DATABASE_URL -c "SELECT version();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Connection successful!"
else
    echo "❌ Cannot connect to database. Check your DATABASE_URL"
    exit 1
fi
echo ""
echo "Press Enter for next step..."
read

# Step 2: Create database roles
echo "👥 Step 2: Creating database roles..."
echo "This will create roles like admin, sales_user, finance_user, etc."
echo "Press Enter to create roles or Ctrl+C to cancel..."
read

psql $DATABASE_URL -f database/enterprise-v2/00-preparation/01_create_roles.sql
echo "✅ Roles created!"
echo ""
echo "Press Enter for next step..."
read

# Step 3: Create schemas only
echo "📁 Step 3: Creating schemas (master, inventory, sales, etc.)..."
echo "This will create 12 schemas including testing and api"
echo "Press Enter to create schemas or Ctrl+C to cancel..."
read

psql $DATABASE_URL -f database/enterprise-v2/01-schemas/01_create_all_schemas.sql
echo "✅ Schemas created!"
echo ""

# Step 4: Show what will be created
echo "📋 Step 4: Preview - The following will be created:"
echo "  - 135 tables across all schemas"
echo "  - 75+ triggers for business automation"
echo "  - 50+ business functions"
echo "  - 40+ API endpoints"
echo ""
echo "Want to see the table list? (y/n)"
read answer
if [ "$answer" = "y" ]; then
    echo "Major tables include:"
    echo "  - master: products, customers, suppliers, branches"
    echo "  - inventory: stock_ledger, batches, stock_allocation"
    echo "  - sales: invoices, invoice_items, sales_orders"
    echo "  - financial: journal_entries, chart_of_accounts"
    echo "  - gst: gst_returns, e_way_bills"
    echo "  ... and 120+ more"
fi
echo ""
echo "Press Enter to create all tables or Ctrl+C to cancel..."
read

# Step 5: Create tables
echo "🏗️  Step 5: Creating all tables..."
psql $DATABASE_URL -f database/enterprise-v2/02-tables/01_master_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/02_party_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/03_inventory_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/04_sales_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/05_procurement_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/06_financial_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/07_gst_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/08_compliance_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/09_analytics_tables.sql
psql $DATABASE_URL -f database/enterprise-v2/02-tables/10_system_tables.sql
echo "✅ All tables created!"

echo ""
echo "Adding foreign key constraints..."
psql $DATABASE_URL -f database/enterprise-v2/02-tables/99_add_foreign_keys.sql
echo "✅ All tables created successfully with foreign keys!"


# Step 6: Grant permissions to roles
echo ""
echo "🔐 Step 6: Granting permissions to roles..."
echo "This will grant appropriate permissions to all roles"
echo "Press Enter to grant permissions or Ctrl+C to skip..."
read

psql $DATABASE_URL -f database/enterprise-v2/00-preparation/02_grant_permissions.sql
echo "✅ Permissions granted!"

# Step 7: Check what was created
echo ""
echo "📊 Step 7: Verification - here's what was created:"
psql $DATABASE_URL -c "
SELECT 
    schemaname as schema,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname IN ('master', 'inventory', 'parties', 'sales', 'procurement', 'financial', 'gst', 'compliance', 'analytics', 'system_config')
GROUP BY schemaname
ORDER BY schemaname;"

echo ""
echo "Press Enter to create triggers or Ctrl+C to stop here..."
read

# Step 8: Create triggers
echo "🔧 Step 8: Creating business automation triggers..."
for file in database/enterprise-v2/04-triggers/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file"
done
echo "✅ Triggers created!"

echo ""
echo "Triggers deployed:"
psql $DATABASE_URL -c "SELECT COUNT(*) as trigger_count FROM pg_trigger WHERE tgname LIKE 'trigger_%';"

echo ""
echo "Press Enter to create business functions or Ctrl+C to stop here..."
read

# Step 9: Create functions
echo "⚡ Step 9: Creating business functions..."
for file in database/enterprise-v2/05-functions/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file"
done
echo "✅ Functions created!"

echo ""
echo "Press Enter to create performance indexes or Ctrl+C to stop here..."
read

# Step 10: Create indexes
echo "🚀 Step 10: Creating performance indexes..."
psql $DATABASE_URL -f database/enterprise-v2/06-indexes/01_performance_indexes.sql
echo "✅ Indexes created!"

echo ""
echo "Press Enter to create API endpoints or Ctrl+C to stop here..."
read

# Step 11: Create APIs
echo "🔌 Step 11: Creating API endpoints..."
for file in database/enterprise-v2/07-api/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file"
done
echo "✅ APIs created!"

echo ""
echo "Press Enter to load initial data or Ctrl+C to stop here..."
read

# Step 12: Load master data
echo "📦 Step 12: Loading initial master data..."
echo "This includes: default organization, UOMs, roles, admin user, etc."
echo "Press Enter to continue..."
read

psql $DATABASE_URL -f database/enterprise-v2/08-initial-data/01_master_data.sql
echo "✅ Master data loaded!"

echo ""
echo "🎉 Basic deployment complete!"
echo ""
echo "Optional: Load sample products? (y/n)"
read answer
if [ "$answer" = "y" ]; then
    psql $DATABASE_URL -f database/enterprise-v2/08-initial-data/02_sample_products.sql
    echo "✅ Sample products loaded!"
fi

echo ""
echo "🏁 DEPLOYMENT FINISHED!"
echo ""
echo "Final statistics:"
psql $DATABASE_URL << EOF
SELECT 
    'Tables' as type,
    COUNT(*) as count
FROM pg_tables 
WHERE schemaname IN ('master', 'inventory', 'parties', 'sales', 'procurement', 'financial', 'gst', 'compliance', 'analytics', 'system_config')
UNION ALL
SELECT 
    'Triggers' as type,
    COUNT(*) as count
FROM pg_trigger 
WHERE tgname LIKE 'trg_%'
UNION ALL
SELECT 
    'API Functions' as type,
    COUNT(*) as count
FROM pg_proc 
WHERE pronamespace::regnamespace::text = 'api';
EOF

echo ""
echo "Test your deployment:"
echo "psql \$DATABASE_URL -c \"SELECT * FROM api.get_products(1, 1, 10);\""