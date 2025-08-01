#!/bin/bash

# =============================================
# ENTERPRISE PHARMA BACKEND - COMPLETE DEPLOYMENT
# =============================================
# This script deploys the entire database in one go
# Make sure DATABASE_URL is set before running
# =============================================

set -e  # Exit on error

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

# Track errors
error_count=0
error_log=""

# Function to run SQL and check for errors
run_sql() {
    local file=$1
    local description=$2
    echo "  → $description"
    # Run the SQL and capture both output and errors
    output=$(psql $DATABASE_URL -f "$file" 2>&1)
    exit_code=$?
    
    # Check for errors
    if [ $exit_code -ne 0 ] || echo "$output" | grep -E "(ERROR|FATAL)" > /dev/null; then
        echo "  ❌ Error in $file:"
        echo "$output" | grep -E "(ERROR|FATAL|LINE|DETAIL|HINT)" | head -20
        echo ""
        error_count=$((error_count + 1))
        error_log="${error_log}\n\n=== Error in $file ===\n$output"
    elif echo "$output" | grep -E "(WARNING|NOTICE)" > /dev/null; then
        # Show warnings but don't stop
        echo "  ⚠️  Warnings in $file:"
        echo "$output" | grep -E "(WARNING|NOTICE)" | head -5
    else
        echo "  ✅ Success"
    fi
}

# Start deployment
echo "🗑️  Step 1: Cleaning existing schemas..."
cleanup_output=$(psql $DATABASE_URL << 'EOF' 2>&1
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
)
if [ $? -ne 0 ]; then
    echo "  ❌ Error during cleanup:"
    echo "$cleanup_output" | grep -E "(ERROR|FATAL)" | head -10
    error_count=$((error_count + 1))
    error_log="${error_log}\n\n=== Error during cleanup ===\n$cleanup_output"
fi
echo "✅ Clean slate ready"

echo ""
echo "👥 Step 2: Creating database roles..."
run_sql "database/enterprise-v2/00-preparation/01_create_roles.sql" "Creating roles"
echo "✅ Roles created"

echo ""
echo "📁 Step 3: Creating schemas..."
run_sql "database/enterprise-v2/01-schemas/01_create_all_schemas.sql" "Creating 12 schemas"
echo "✅ Schemas created"

echo ""
echo "🏗️  Step 4: Creating tables..."
run_sql "database/enterprise-v2/02-tables/01_master_tables.sql" "Master tables"
run_sql "database/enterprise-v2/02-tables/02_party_tables.sql" "Party tables"
run_sql "database/enterprise-v2/02-tables/03_inventory_tables.sql" "Inventory tables"
run_sql "database/enterprise-v2/02-tables/04_sales_tables.sql" "Sales tables"
run_sql "database/enterprise-v2/02-tables/05_procurement_tables.sql" "Procurement tables"
run_sql "database/enterprise-v2/02-tables/06_financial_tables.sql" "Financial tables"
run_sql "database/enterprise-v2/02-tables/07_gst_tables.sql" "GST tables"
run_sql "database/enterprise-v2/02-tables/08_compliance_tables.sql" "Compliance tables"
run_sql "database/enterprise-v2/02-tables/09_analytics_tables.sql" "Analytics tables"
run_sql "database/enterprise-v2/02-tables/10_system_tables.sql" "System tables"
run_sql "database/enterprise-v2/02-tables/99_add_foreign_keys.sql" "Foreign keys"
echo "✅ All tables created"

echo ""
echo "🔐 Step 5: Granting permissions..."
run_sql "database/enterprise-v2/00-preparation/02_grant_permissions.sql" "Granting permissions"
echo "✅ Permissions granted"

echo ""
echo "🔧 Step 6: Creating triggers..."
# Run cleanup first
run_sql "database/enterprise-v2/04-triggers/00_cleanup_duplicates.sql" "Cleaning up duplicates"
# Then run all other trigger files
for file in database/enterprise-v2/04-triggers/*.sql; do
    if [ -f "$file" ] && [ "$file" != "database/enterprise-v2/04-triggers/00_cleanup_duplicates.sql" ]; then
        run_sql "$file" "$(basename $file)"
    fi
done
echo "✅ Triggers created"

echo ""
echo "⚡ Step 7: Creating business functions..."
for file in database/enterprise-v2/05-functions/*.sql; do
    if [ -f "$file" ]; then
        run_sql "$file" "$(basename $file)"
    fi
done
echo "✅ Functions created"

echo ""
echo "🚀 Step 8: Creating performance indexes..."
run_sql "database/enterprise-v2/06-indexes/01_performance_indexes.sql" "Performance indexes"
echo "✅ Indexes created"

echo ""
echo "🔌 Step 9: Creating API endpoints..."
for file in database/enterprise-v2/07-api/*.sql; do
    if [ -f "$file" ]; then
        run_sql "$file" "$(basename $file)"
    fi
done
echo "✅ APIs created"

echo ""
echo "📦 Step 10: Loading initial data..."
run_sql "database/enterprise-v2/08-initial-data/01_master_data.sql" "Master data"
echo "✅ Master data loaded"

echo ""
echo "🎯 Step 11: Loading sample products (optional)..."
if [ "$LOAD_SAMPLE_DATA" = "true" ]; then
    run_sql "database/enterprise-v2/08-initial-data/02_sample_products.sql" "Sample products"
    echo "✅ Sample products loaded"
else
    echo "⏭️  Skipped (set LOAD_SAMPLE_DATA=true to load)"
fi

echo ""
echo "📊 Deployment Summary:"
echo "===================="

# Show statistics
psql $DATABASE_URL << EOF
SELECT 
    schemaname as schema,
    COUNT(*) as tables
FROM pg_tables 
WHERE schemaname IN ('master', 'inventory', 'parties', 'sales', 'procurement', 'financial', 'gst', 'compliance', 'analytics', 'system_config')
GROUP BY schemaname
ORDER BY schemaname;

SELECT 
    COUNT(*) as total_triggers
FROM pg_trigger 
WHERE tgname LIKE 'trg_%';

SELECT 
    COUNT(*) as api_functions
FROM pg_proc 
WHERE pronamespace::regnamespace::text = 'api';

SELECT 
    COUNT(*) as total_indexes
FROM pg_indexes
WHERE schemaname IN ('master', 'inventory', 'parties', 'sales', 'procurement', 'financial', 'gst', 'compliance', 'analytics', 'system_config');
EOF

echo ""
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: Admin@123"
echo ""
echo "Test the deployment:"
echo "psql \$DATABASE_URL -c \"SELECT * FROM master.organizations;\""
echo ""

# Check if there were any notices/warnings
if [ -f deployment.log ]; then
    echo "⚠️  Check deployment.log for any warnings"
fi

# Show error summary
if [ $error_count -gt 0 ]; then
    echo ""
    echo "❌ DEPLOYMENT COMPLETED WITH $error_count ERRORS"
    echo "================================="
    echo ""
    echo "Full error log saved to: deployment-errors.log"
    echo "$error_log" > deployment-errors.log
    echo ""
    echo "To see all errors:"
    echo "cat deployment-errors.log"
    exit 1
else
    echo ""
    echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY WITH NO ERRORS!"
    exit 0
fi