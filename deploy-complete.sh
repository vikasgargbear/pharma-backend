#!/bin/bash

# Complete deployment script for Enterprise Pharma Backend

echo "🚀 Enterprise Pharma Backend - Complete Deployment"
echo "=================================================="
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
    echo "Resetting database..."
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
fi

echo ""
echo "Starting deployment..."

# Step 0: Create roles
echo "0️⃣ Creating database roles..."
psql $DATABASE_URL -f database/enterprise-v2/00-preparation/01_create_roles.sql 2>&1 | grep -v "already exists" || true
echo "✅ Roles created"

# Step 1: Create schemas
echo "1️⃣ Creating schemas..."
psql $DATABASE_URL -f database/enterprise-v2/01-schemas/01_create_all_schemas.sql
echo "✅ Schemas created"

# Step 2: Create all tables (with CREATE TABLE IF NOT EXISTS)
echo ""
echo "2️⃣ Creating tables..."
psql $DATABASE_URL -f database/enterprise-v2/02-tables/01_master_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/03_party_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/02_inventory_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/04_sales_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/05_procurement_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/06_financial_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/07_gst_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/08_compliance_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/09_analytics_tables.sql 2>&1 | grep -v "already exists" || true
psql $DATABASE_URL -f database/enterprise-v2/02-tables/10_system_tables.sql 2>&1 | grep -v "already exists" || true
echo "✅ Tables created"

# Step 3: Grant permissions to roles
echo ""
echo "3️⃣ Granting permissions to roles..."
psql $DATABASE_URL -f database/enterprise-v2/00-preparation/02_grant_permissions.sql 2>&1 | grep -v "already exists" || true
echo "✅ Permissions granted"

# Step 4: Add foreign key constraints
echo ""
echo "4️⃣ Adding foreign key constraints..."
psql $DATABASE_URL -f database/enterprise-v2/02-tables/99_add_foreign_keys.sql 2>&1 | grep -v "already exists" || true
echo "✅ Foreign keys added"

# Step 5: Create triggers
echo ""
echo "5️⃣ Creating triggers..."
for file in database/enterprise-v2/04-triggers/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file" 2>&1 | grep -v "already exists" || true
done
echo "✅ Triggers created"

# Step 6: Create functions
echo ""
echo "6️⃣ Creating business functions..."
for file in database/enterprise-v2/05-functions/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file" 2>&1 | grep -v "already exists" || true
done
echo "✅ Functions created"

# Step 7: Create indexes
echo ""
echo "7️⃣ Creating performance indexes..."
psql $DATABASE_URL -f database/enterprise-v2/06-indexes/01_performance_indexes.sql 2>&1 | grep -v "already exists" || true
echo "✅ Indexes created"

# Step 8: Create APIs
echo ""
echo "8️⃣ Creating API functions..."
for file in database/enterprise-v2/08-api/*.sql; do
    echo "Loading: $(basename $file)"
    psql $DATABASE_URL -f "$file" 2>&1 | grep -v "already exists" || true
done
echo "✅ APIs created"

# Step 9: Load initial data
echo ""
echo "9️⃣ Loading initial data..."
psql $DATABASE_URL -f database/enterprise-v2/07-initial-data/01_master_data.sql 2>&1 | grep -v "duplicate key" || true
echo "✅ Initial data loaded"

# Step 10: Verify deployment
echo ""
echo "🔍 Verifying deployment..."
psql $DATABASE_URL << EOF
SELECT 
    schemaname as schema,
    COUNT(*) as tables
FROM pg_tables 
WHERE schemaname IN ('master', 'inventory', 'parties', 'sales', 'procurement', 'financial', 'gst', 'compliance', 'analytics', 'system_config')
GROUP BY schemaname
ORDER BY schemaname;

SELECT 
    'Total Triggers' as metric,
    COUNT(*) as count 
FROM pg_trigger 
WHERE tgname LIKE 'trigger_%'
UNION ALL
SELECT 
    'Total API Functions' as metric,
    COUNT(*) as count 
FROM pg_proc 
WHERE pronamespace::regnamespace::text = 'api';
EOF

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Test your deployment:"
echo "psql \$DATABASE_URL -c \"SELECT * FROM api.get_products(1, 1, 10);\""