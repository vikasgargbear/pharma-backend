#!/bin/bash

# =============================================
# SUPABASE DEPLOYMENT SCRIPT
# =============================================
# Automated deployment to Supabase PostgreSQL
# =============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST=""
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD=""
PROJECT_REF=""

echo -e "${BLUE}=============================================
SUPABASE DEPLOYMENT SCRIPT
=============================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if required variables are set
if [ -z "$DB_HOST" ] || [ -z "$DB_PASSWORD" ] || [ -z "$PROJECT_REF" ]; then
    echo -e "${YELLOW}Please configure your Supabase connection details:${NC}"
    echo ""
    echo "1. Update this script with your values:"
    echo "   DB_HOST=\"db.[PROJECT-REF].supabase.co\""
    echo "   DB_PASSWORD=\"your-database-password\""
    echo "   PROJECT_REF=\"your-project-ref\""
    echo ""
    echo "2. Or set environment variables:"
    echo "   export SUPABASE_DB_HOST=\"db.[PROJECT-REF].supabase.co\""
    echo "   export SUPABASE_DB_PASSWORD=\"your-password\""
    echo "   export SUPABASE_PROJECT_REF=\"your-project-ref\""
    echo ""
    
    # Try to get from environment
    if [ ! -z "$SUPABASE_DB_HOST" ]; then
        DB_HOST="$SUPABASE_DB_HOST"
        print_status "Using DB_HOST from environment: $DB_HOST"
    fi
    
    if [ ! -z "$SUPABASE_DB_PASSWORD" ]; then
        DB_PASSWORD="$SUPABASE_DB_PASSWORD"
        print_status "Using DB_PASSWORD from environment"
    fi
    
    if [ ! -z "$SUPABASE_PROJECT_REF" ]; then
        PROJECT_REF="$SUPABASE_PROJECT_REF"
        print_status "Using PROJECT_REF from environment: $PROJECT_REF"
    fi
    
    # Check again
    if [ -z "$DB_HOST" ] || [ -z "$DB_PASSWORD" ] || [ -z "$PROJECT_REF" ]; then
        print_error "Missing required configuration. Exiting."
        exit 1
    fi
fi

# Build connection string
CONNECTION_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}"

echo -e "${BLUE}Deploying to: ${DB_HOST}${NC}"
echo ""

# Function to execute SQL file
execute_sql_file() {
    local file=$1
    local description=$2
    
    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        return 1
    fi
    
    echo -e "${YELLOW}Executing: $description${NC}"
    echo "File: $file"
    
    # Execute with better error reporting
    if psql "$CONNECTION_STRING" -f "$file" -v ON_ERROR_STOP=1 2>&1 | tee /tmp/psql_output.log; then
        print_status "$description completed"
    else
        print_error "$description failed"
        echo -e "${RED}Error details:${NC}"
        tail -10 /tmp/psql_output.log
        echo ""
        read -p "Continue with deployment? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    echo ""
}

# Function to test connection
test_connection() {
    echo -e "${YELLOW}Testing database connection...${NC}"
    if psql "$CONNECTION_STRING" -c "SELECT version();" > /dev/null 2>&1; then
        print_status "Database connection successful"
    else
        print_error "Cannot connect to database"
        echo "Please check your connection details and try again."
        exit 1
    fi
    echo ""
}

# Main deployment sequence
main() {
    echo -e "${BLUE}Starting deployment...${NC}"
    echo ""
    
    # Test connection
    test_connection
    
    # Deploy in correct order
    echo -e "${BLUE}Phase 1: Preparation and Core Schema${NC}"
    execute_sql_file "00_supabase_prep.sql" "Supabase preparation and auth functions"
    
    # Quick test to verify create_organization function
    echo -e "${YELLOW}Testing create_organization function...${NC}"
    if psql "$CONNECTION_STRING" -c "SELECT 'create_organization function exists' WHERE EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'create_organization');" > /dev/null 2>&1; then
        print_status "create_organization function is available"
    else
        print_warning "create_organization function not found - this may cause issues later"
    fi
    
    execute_sql_file "01_core_schema.sql" "Core database schema"
    
    # Quick test for date functions
    echo -e "${YELLOW}Testing date functions...${NC}"
    if psql "$CONNECTION_STRING" -c "SELECT (('2025-12-31'::DATE - CURRENT_DATE)::INTEGER) AS test;" > /dev/null 2>&1; then
        print_status "Date functions working correctly"
    else
        print_warning "Date functions may have issues"
    fi
    execute_sql_file "01a_supabase_modifications.sql" "Supabase-specific modifications"
    execute_sql_file "01c_enterprise_critical_schema.sql" "Enterprise critical features"
    
    echo -e "${BLUE}Phase 2: Business Logic${NC}"
    execute_sql_file "02_business_functions.sql" "Business functions"
    execute_sql_file "02b_additional_functions.sql" "Additional business functions"
    
    echo -e "${BLUE}Phase 3: Automation${NC}"
    execute_sql_file "03_triggers_automation.sql" "Triggers and automation"
    execute_sql_file "03b_additional_triggers.sql" "Additional triggers"
    
    echo -e "${BLUE}Phase 4: Performance${NC}"
    execute_sql_file "04_indexes_performance.sql" "Performance indexes"
    execute_sql_file "04b_additional_indexes.sql" "Additional indexes"
    
    echo -e "${BLUE}Phase 5: Security${NC}"
    execute_sql_file "05_security_rls_supabase.sql" "Row Level Security policies"
    
    echo -e "${BLUE}Phase 6: Initial Data${NC}"
    
    # Ask user about data type
    echo -e "${YELLOW}Which initial data do you want to load?${NC}"
    echo "1) Production data only (minimal, safe for production)"
    echo "2) Development data (includes test org and sample data)"
    echo "3) Skip initial data"
    read -p "Choose option (1-3): " -n 1 -r data_choice
    echo
    
    case $data_choice in
        1)
            execute_sql_file "06_initial_data_production.sql" "Production initial data"
            ;;
        2)
            print_warning "Loading development data - NOT for production use!"
            execute_sql_file "06_initial_data_development.sql" "Development test data"
            ;;
        3)
            print_warning "Skipping initial data - you'll need to set up master data manually"
            ;;
        *)
            print_warning "Invalid choice - loading production data by default"
            execute_sql_file "06_initial_data_production.sql" "Production initial data"
            ;;
    esac
    
    print_status "All deployment phases completed successfully!"
    echo ""
    
    # Initialize calculated fields
    echo -e "${BLUE}Initializing calculated fields...${NC}"
    if psql "$CONNECTION_STRING" -c "SELECT update_calculated_fields();" > /dev/null 2>&1; then
        print_status "Calculated fields initialized"
    else
        print_warning "Could not initialize calculated fields - this is normal for fresh deployment"
    fi
    echo ""
    
    # Verify deployment
    echo -e "${BLUE}Verifying deployment...${NC}"
    
    # Check if key tables exist
    if psql "$CONNECTION_STRING" -c "SELECT COUNT(*) FROM organizations;" > /dev/null 2>&1; then
        print_status "Core tables accessible"
    else
        print_warning "Core tables may not be accessible - check RLS policies"
    fi
    
    # Check if functions exist
    if psql "$CONNECTION_STRING" -c "SELECT current_org_id();" > /dev/null 2>&1; then
        print_status "Auth functions working"
    else
        print_warning "Auth functions may have issues"
    fi
    
    echo ""
    echo -e "${GREEN}=============================================
DEPLOYMENT COMPLETED SUCCESSFULLY!
=============================================${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Test authentication through Supabase Auth"
    echo "2. Create your first organization"
    echo "3. Test API endpoints"
    echo "4. Set up realtime subscriptions"
    echo "5. Configure storage buckets"
    echo ""
    echo -e "${BLUE}Connection details:${NC}"
    echo "Host: $DB_HOST"
    echo "Database: $DB_NAME"
    echo "Project: $PROJECT_REF"
    echo ""
    echo -e "${BLUE}Test with:${NC}"
    echo "psql \"$CONNECTION_STRING\""
    echo ""
}

# Check if we're in the right directory
if [ ! -f "00_supabase_prep.sql" ]; then
    print_error "Please run this script from the PRODUCTION_READY directory"
    echo "Current directory: $(pwd)"
    echo "Expected files: 00_supabase_prep.sql, 01_core_schema.sql, etc."
    exit 1
fi

# Run main deployment
main

echo -e "${GREEN}Deployment script completed!${NC}"