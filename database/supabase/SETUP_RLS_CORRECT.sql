-- =============================================
-- CORRECT RLS SETUP BASED ON ACTUAL TABLE SCHEMA
-- =============================================
-- Using the actual table structures from PRODUCTION_TABLE_SCHEMAS.md
-- =============================================

-- =============================================
-- STEP 1: Enable RLS on ALL Tables
-- =============================================

-- Core Business Tables
ALTER TABLE org_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Financial Tables
ALTER TABLE invoice_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_outstanding ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_outstanding ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entry_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;

-- Purchase/Supply Chain
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_returns ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_return_items ENABLE ROW LEVEL SECURITY;

-- Sales & Returns
ALTER TABLE sales_returns ENABLE ROW LEVEL SECURITY;
ALTER TABLE return_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE challans ENABLE ROW LEVEL SECURITY;
ALTER TABLE challan_items ENABLE ROW LEVEL SECURITY;

-- Inventory & Stock
ALTER TABLE inventory_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_transfer_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_locations ENABLE ROW LEVEL SECURITY;

-- Master Data
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE units_of_measure ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_uom_conversions ENABLE ROW LEVEL SECURITY;

-- Compliance & Regulatory
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE narcotic_register ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_checks ENABLE ROW LEVEL SECURITY;

-- Loyalty & Schemes
ALTER TABLE discount_schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE discount_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE discount_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE applied_discounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE loyalty_accounts ENABLE ROW LEVEL SECURITY;

-- System Tables
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_log ENABLE ROW LEVEL SECURITY;

-- Drop ALL existing policies to start fresh
DO $$ 
DECLARE
    pol RECORD;
BEGIN
    -- Drop all existing policies on our main tables
    FOR pol IN 
        SELECT policyname, tablename 
        FROM pg_policies 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename);
    END LOOP;
END $$;

-- =============================================
-- STEP 2: Create Basic Authenticated Access Policies
-- =============================================
-- For now, all authenticated users can access everything
-- This is better than public access but still needs refinement

-- ORG_USERS - All authenticated users can manage users
CREATE POLICY "auth_users_all_ops" ON org_users
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- PRODUCTS - All authenticated users can manage products
CREATE POLICY "auth_products_all_ops" ON products
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- CUSTOMERS - All authenticated users can manage customers
CREATE POLICY "auth_customers_all_ops" ON customers
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- ORDERS - All authenticated users can manage orders
CREATE POLICY "auth_orders_all_ops" ON orders
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- INVOICES - All authenticated users can view/create, no delete
CREATE POLICY "auth_invoices_select" ON invoices
    FOR SELECT TO authenticated 
    USING (true);

CREATE POLICY "auth_invoices_insert" ON invoices
    FOR INSERT TO authenticated 
    WITH CHECK (true);

CREATE POLICY "auth_invoices_update" ON invoices
    FOR UPDATE TO authenticated 
    USING (true);
-- No DELETE policy = invoices cannot be deleted (audit trail)

-- BATCHES - All authenticated users can manage batches
CREATE POLICY "auth_batches_all_ops" ON batches
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- INVENTORY_MOVEMENTS - View and insert only, no update/delete
CREATE POLICY "auth_inventory_select" ON inventory_movements
    FOR SELECT TO authenticated 
    USING (true);

CREATE POLICY "auth_inventory_insert" ON inventory_movements
    FOR INSERT TO authenticated 
    WITH CHECK (true);
-- No UPDATE/DELETE = movements are immutable

-- PAYMENTS - All authenticated users can manage payments
CREATE POLICY "auth_payments_all_ops" ON payments
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- ORDER_ITEMS - Follow order access
CREATE POLICY "auth_order_items_all_ops" ON order_items
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- SUPPLIERS - All authenticated users can manage suppliers
CREATE POLICY "auth_suppliers_all_ops" ON suppliers
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- PURCHASES - All authenticated users can manage purchases
CREATE POLICY "auth_purchases_all_ops" ON purchases
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- PURCHASE_ITEMS - All authenticated users can manage purchase items
CREATE POLICY "auth_purchase_items_all_ops" ON purchase_items
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- CHALLANS - All authenticated users can manage challans
CREATE POLICY "auth_challans_all_ops" ON challans
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- CHALLAN_ITEMS - All authenticated users can manage challan items
CREATE POLICY "auth_challan_items_all_ops" ON challan_items
    FOR ALL TO authenticated 
    USING (true) 
    WITH CHECK (true);

-- TAX_ENTRIES - Read-only for all authenticated
CREATE POLICY "auth_tax_entries_read" ON tax_entries
    FOR SELECT TO authenticated 
    USING (true);

-- CATEGORIES - All authenticated users can read
CREATE POLICY "auth_categories_read" ON categories
    FOR SELECT TO authenticated 
    USING (true);

-- UNITS_OF_MEASURE - Read-only for all authenticated
CREATE POLICY "auth_units_read" ON units_of_measure
    FOR SELECT TO authenticated 
    USING (true);

-- Add more tables with basic policies to prevent public access
-- Financial
CREATE POLICY "auth_invoice_payments_all" ON invoice_payments FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_customer_outstanding_all" ON customer_outstanding FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_supplier_outstanding_all" ON supplier_outstanding FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Inventory
CREATE POLICY "auth_inventory_transactions_all" ON inventory_transactions FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_stock_transfers_all" ON stock_transfers FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_stock_transfer_items_all" ON stock_transfer_items FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- Returns
CREATE POLICY "auth_sales_returns_all" ON sales_returns FOR ALL TO authenticated USING (true) WITH CHECK (true);
CREATE POLICY "auth_purchase_returns_all" ON purchase_returns FOR ALL TO authenticated USING (true) WITH CHECK (true);

-- System tables - restricted
CREATE POLICY "auth_audit_logs_read" ON audit_logs FOR SELECT TO authenticated USING (true);
CREATE POLICY "auth_activity_log_read" ON activity_log FOR SELECT TO authenticated USING (true);

-- =============================================
-- STEP 3: Public Access (Minimal)
-- =============================================

-- Allow public to read organizations (for login screen)
-- First check if policy exists, then create if needed
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'organizations' 
        AND policyname = 'public_read_orgs'
    ) THEN
        CREATE POLICY "public_read_orgs" ON organizations
            FOR SELECT TO anon 
            USING (is_active = true);
    END IF;
END $$;

-- =============================================
-- STEP 4: Verify RLS Status
-- =============================================

-- Check which critical tables have RLS enabled
SELECT 
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN '✅ RLS Enabled'
        ELSE '❌ RLS Disabled - SECURITY RISK!'
    END as security_status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
    'org_users', 'products', 'customers', 'orders', 
    'invoices', 'batches', 'inventory_movements', 'payments',
    'suppliers', 'purchases', 'challans'
)
ORDER BY rowsecurity DESC, tablename;

-- Count policies by table
SELECT 
    tablename,
    COUNT(*) as policy_count,
    string_agg(policyname, ', ') as policies
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- =============================================
-- STEP 5: Enable RLS on ALL Remaining Tables
-- =============================================
-- This ensures NO table is left unsecured

DO $$ 
DECLARE
    tbl RECORD;
BEGIN
    -- Enable RLS on all public tables that don't have it
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND rowsecurity = false
        AND tablename NOT IN ('schema_migrations', 'spatial_ref_sys')
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl.tablename);
        
        -- Create a basic policy for authenticated access
        -- Check if policy already exists before creating
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = tbl.tablename 
            AND policyname = 'auth_basic_access'
        ) THEN
            EXECUTE format('CREATE POLICY auth_basic_access ON %I FOR ALL TO authenticated USING (true) WITH CHECK (true)', tbl.tablename);
        END IF;
    END LOOP;
END $$;

-- =============================================
-- STEP 6: Final Security Check
-- =============================================

-- Show ALL tables and their RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    CASE 
        WHEN rowsecurity THEN '✅ SECURED'
        ELSE '❌ UNSECURED - PUBLIC ACCESS!'
    END as security_status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY rowsecurity ASC, tablename;

-- Show policy count per table
SELECT 
    tablename,
    COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY COUNT(*) DESC, tablename;

-- =============================================
-- STEP 7: Test Queries
-- =============================================

-- These should work for authenticated users:
/*
SELECT COUNT(*) as user_count FROM org_users;
SELECT COUNT(*) as product_count FROM products;
SELECT COUNT(*) as customer_count FROM customers;
SELECT COUNT(*) as order_count FROM orders;
SELECT COUNT(*) as invoice_count FROM invoices;
*/

-- This should fail (no delete policy on invoices):
/*
DELETE FROM invoices WHERE invoice_id = 1;
-- ERROR: new row violates row-level security policy
*/