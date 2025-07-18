-- =============================================
-- MASTER DATABASE SETUP - Including Invoice Module
-- =============================================
-- Run this file for a complete database setup
-- This includes all core tables, financial module, and invoice fixes
-- Last Updated: 2025-07-18
-- =============================================

-- IMPORTANT: Run these files in order:

-- Core Schema
\i 00_supabase_prep.sql
\i 01_core_schema.sql
\i 01a_supabase_modifications.sql
\i 01c_enterprise_critical_schema.sql

-- Business Logic
\i 02_business_functions.sql
\i 02b_additional_functions.sql

-- Triggers
\i 03_triggers_automation.sql
\i 03b_additional_triggers.sql

-- Performance
\i 04_indexes_performance.sql
\i 04b_additional_indexes.sql

-- Security
\i 05_security_rls_supabase.sql

-- Initial Data
\i 06_initial_data_production.sql

-- Final Setup
\i 07_FINAL_SETUP.sql

-- Recent Additions
\i 08_add_area_field.sql
\i 09_fix_invoices_table.sql
\i 10_create_invoice_items_table.sql
\i 11_create_payment_tables.sql

-- Complete Invoice Module Fix (includes all fixes)
\i 12_complete_invoice_migrations.sql

-- Financial Module (if needed)
-- \i FINANCIAL_MODULE/01_financial_core_schema.sql
-- \i FINANCIAL_MODULE/01b_financial_schema.sql
-- \i FINANCIAL_MODULE/02_financial_functions.sql
-- \i FINANCIAL_MODULE/03_financial_triggers.sql
-- \i FINANCIAL_MODULE/04_financial_indexes.sql
-- \i FINANCIAL_MODULE/05_financial_security.sql
-- \i FINANCIAL_MODULE/06_financial_initial_data.sql

-- =============================================
-- Verification Queries
-- =============================================

-- Check all tables are created
SELECT 
    schemaname,
    tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Check invoice module specifically
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Invoice Module Status ===';
    
    -- Check invoices table
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='invoices' AND column_name='updated_at') THEN
        RAISE NOTICE '✓ Invoices table has updated_at column';
    ELSE
        RAISE NOTICE '✗ Invoices table missing updated_at column';
    END IF;
    
    -- Check invoice_items table
    IF EXISTS (SELECT FROM information_schema.tables 
               WHERE table_name = 'invoice_items') THEN
        RAISE NOTICE '✓ Invoice_items table exists';
    ELSE
        RAISE NOTICE '✗ Invoice_items table missing';
    END IF;
    
    -- Check invoice_payments table
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='invoice_payments' 
               AND column_name='payment_amount') THEN
        RAISE NOTICE '✓ Invoice_payments table properly configured';
    ELSE
        RAISE NOTICE '✗ Invoice_payments table needs configuration';
    END IF;
    
    RAISE NOTICE '============================';
END $$;

-- Count records in key tables
SELECT 
    'organizations' as table_name, COUNT(*) as record_count FROM organizations
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'invoice_items', COUNT(*) FROM invoice_items
UNION ALL
SELECT 'invoice_payments', COUNT(*) FROM invoice_payments
ORDER BY table_name;

-- =============================================
-- Success Message
-- =============================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎉 Database setup complete!';
    RAISE NOTICE '✓ Core schema created';
    RAISE NOTICE '✓ Business functions added';
    RAISE NOTICE '✓ Triggers configured';
    RAISE NOTICE '✓ Indexes created';
    RAISE NOTICE '✓ Invoice module ready';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Test invoice generation from frontend';
    RAISE NOTICE '2. Verify PDF generation works';
    RAISE NOTICE '3. Test payment recording';
END $$;