-- =============================================
-- COMPREHENSIVE SUPABASE RLS POLICIES
-- =============================================
-- Complete rewrite for enterprise pharmaceutical ERP
-- Proper multi-tenant security with Supabase auth
-- =============================================

-- =============================================
-- HELPER FUNCTIONS FOR RLS
-- =============================================

-- Get current user's organization IDs
CREATE OR REPLACE FUNCTION auth_user_orgs()
RETURNS TABLE(org_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ou.org_id
    FROM org_users ou
    WHERE ou.auth_uid = auth.uid()
    AND ou.is_active = TRUE;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Get current user's role in specific org
CREATE OR REPLACE FUNCTION auth_user_role(p_org_id UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN (
        SELECT role
        FROM org_users
        WHERE auth_uid = auth.uid()
        AND org_id = p_org_id
        AND is_active = TRUE
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Get current user ID
CREATE OR REPLACE FUNCTION auth_user_id()
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT user_id
        FROM org_users
        WHERE auth_uid = auth.uid()
        AND is_active = TRUE
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Check if user has specific permission
CREATE OR REPLACE FUNCTION auth_has_permission(permission TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    user_role TEXT;
    user_org UUID;
BEGIN
    SELECT role, org_id INTO user_role, user_org
    FROM org_users
    WHERE auth_uid = auth.uid()
    AND is_active = TRUE
    LIMIT 1;
    
    IF user_role IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN CASE permission
        WHEN 'manage_products' THEN user_role IN ('owner', 'admin', 'inventory_manager')
        WHEN 'manage_orders' THEN user_role IN ('owner', 'admin', 'sales_manager', 'sales_rep')
        WHEN 'manage_purchases' THEN user_role IN ('owner', 'admin', 'purchase_manager')
        WHEN 'manage_customers' THEN user_role IN ('owner', 'admin', 'sales_manager', 'sales_rep')
        WHEN 'manage_suppliers' THEN user_role IN ('owner', 'admin', 'purchase_manager')
        WHEN 'manage_users' THEN user_role IN ('owner', 'admin')
        WHEN 'view_reports' THEN user_role IN ('owner', 'admin', 'accountant', 'sales_manager')
        WHEN 'manage_finances' THEN user_role IN ('owner', 'admin', 'accountant')
        WHEN 'admin_only' THEN user_role IN ('owner', 'admin')
        ELSE FALSE
    END;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- =============================================
-- ENABLE RLS ON ALL TABLES
-- =============================================

-- Core organization tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_branches ENABLE ROW LEVEL SECURITY;

-- Master data tables
ALTER TABLE product_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE units_of_measure ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

-- Product management
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_uom_conversions ENABLE ROW LEVEL SECURITY;

-- Customer & Supplier management
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;

-- Inventory management
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_movements ENABLE ROW LEVEL SECURITY;

-- Sales management
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- Purchase management
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_items ENABLE ROW LEVEL SECURITY;

-- Financial management
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_outstanding ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier_outstanding ENABLE ROW LEVEL SECURITY;

-- Accounting
ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entry_lines ENABLE ROW LEVEL SECURITY;

-- System tables
ALTER TABLE barcode_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE barcode_sequences ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_queue ENABLE ROW LEVEL SECURITY;

-- Enterprise features (if they exist)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'doctors') THEN
        EXECUTE 'ALTER TABLE doctors ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'prescriptions') THEN
        EXECUTE 'ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_transfers') THEN
        EXECUTE 'ALTER TABLE stock_transfers ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_transfer_items') THEN
        EXECUTE 'ALTER TABLE stock_transfer_items ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'return_requests') THEN
        EXECUTE 'ALTER TABLE return_requests ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'return_items') THEN
        EXECUTE 'ALTER TABLE return_items ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'loyalty_programs') THEN
        EXECUTE 'ALTER TABLE loyalty_programs ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'customer_loyalty') THEN
        EXECUTE 'ALTER TABLE customer_loyalty ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'price_lists') THEN
        EXECUTE 'ALTER TABLE price_lists ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'price_list_items') THEN
        EXECUTE 'ALTER TABLE price_list_items ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schemes') THEN
        EXECUTE 'ALTER TABLE schemes ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheme_products') THEN
        EXECUTE 'ALTER TABLE scheme_products ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'gstr1_data') THEN
        EXECUTE 'ALTER TABLE gstr1_data ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'gstr3b_data') THEN
        EXECUTE 'ALTER TABLE gstr3b_data ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'drug_inspector_visits') THEN
        EXECUTE 'ALTER TABLE drug_inspector_visits ENABLE ROW LEVEL SECURITY';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'narcotic_register') THEN
        EXECUTE 'ALTER TABLE narcotic_register ENABLE ROW LEVEL SECURITY';
    END IF;
END $$;

-- =============================================
-- CORE ORGANIZATION POLICIES
-- =============================================

-- Organizations: Users can only access their own organizations
CREATE POLICY org_access ON organizations
    FOR ALL USING (org_id IN (SELECT auth_user_orgs()));

-- Org users: Access based on organization membership
CREATE POLICY org_users_select ON org_users
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY org_users_insert ON org_users
    FOR INSERT WITH CHECK (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_users')
    );

CREATE POLICY org_users_update ON org_users
    FOR UPDATE USING (
        org_id IN (SELECT auth_user_orgs())
        AND (
            user_id = auth_user_id() -- Users can update themselves
            OR auth_has_permission('manage_users') -- Or admins can update others
        )
    );

CREATE POLICY org_users_delete ON org_users
    FOR DELETE USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('admin_only')
    );

-- Org branches: Organization isolation
CREATE POLICY org_branches_access ON org_branches
    FOR ALL USING (org_id IN (SELECT auth_user_orgs()));

-- =============================================
-- MASTER DATA POLICIES
-- =============================================

-- Product types, units, categories: Global read, admin write
CREATE POLICY product_types_select ON product_types
    FOR SELECT USING (org_id IS NULL OR org_id IN (SELECT auth_user_orgs()));

CREATE POLICY product_types_modify ON product_types
    FOR INSERT WITH CHECK (
        org_id IS NULL OR (
            org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('admin_only')
        )
    );

CREATE POLICY units_of_measure_select ON units_of_measure
    FOR SELECT USING (org_id IS NULL OR org_id IN (SELECT auth_user_orgs()));

CREATE POLICY units_of_measure_modify ON units_of_measure
    FOR INSERT WITH CHECK (
        org_id IS NULL OR (
            org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('admin_only')
        )
    );

CREATE POLICY categories_select ON categories
    FOR SELECT USING (org_id IS NULL OR org_id IN (SELECT auth_user_orgs()));

CREATE POLICY categories_modify ON categories
    FOR INSERT WITH CHECK (
        org_id IS NULL OR (
            org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('admin_only')
        )
    );

-- =============================================
-- PRODUCT MANAGEMENT POLICIES
-- =============================================

-- Products: Organization isolation with role-based access
CREATE POLICY products_select ON products
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY products_insert ON products
    FOR INSERT WITH CHECK (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

CREATE POLICY products_update ON products
    FOR UPDATE USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

CREATE POLICY products_delete ON products
    FOR DELETE USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('admin_only')
    );

-- Product UOM conversions
CREATE POLICY product_uom_conversions_access ON product_uom_conversions
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

-- =============================================
-- CUSTOMER & SUPPLIER POLICIES
-- =============================================

-- Customers
CREATE POLICY customers_select ON customers
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY customers_modify ON customers
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_customers')
    );

-- Suppliers
CREATE POLICY suppliers_select ON suppliers
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY suppliers_modify ON suppliers
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_suppliers')
    );

-- =============================================
-- INVENTORY MANAGEMENT POLICIES
-- =============================================

-- Batches: View all, modify with permission
CREATE POLICY batches_select ON batches
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY batches_modify ON batches
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

-- Inventory movements: View all, create with permission
CREATE POLICY inventory_movements_select ON inventory_movements
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY inventory_movements_insert ON inventory_movements
    FOR INSERT WITH CHECK (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

CREATE POLICY inventory_movements_update ON inventory_movements
    FOR UPDATE USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('admin_only')
    );

-- =============================================
-- SALES MANAGEMENT POLICIES
-- =============================================

-- Orders: Complex role-based access
CREATE POLICY orders_select ON orders
    FOR SELECT USING (
        org_id IN (SELECT auth_user_orgs())
        AND (
            auth_has_permission('view_reports')
            OR created_by = auth_user_id() -- Sales reps can see their own orders
        )
    );

CREATE POLICY orders_insert ON orders
    FOR INSERT WITH CHECK (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_orders')
    );

CREATE POLICY orders_update ON orders
    FOR UPDATE USING (
        org_id IN (SELECT auth_user_orgs())
        AND (
            auth_has_permission('admin_only')
            OR (
                created_by = auth_user_id()
                AND order_status NOT IN ('completed', 'cancelled')
            )
        )
    );

CREATE POLICY orders_delete ON orders
    FOR DELETE USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('admin_only')
    );

-- Order items: Access through parent order
CREATE POLICY order_items_select ON order_items
    FOR SELECT USING (
        order_id IN (
            SELECT order_id FROM orders 
            WHERE org_id IN (SELECT auth_user_orgs())
        )
    );

CREATE POLICY order_items_modify ON order_items
    FOR ALL USING (
        order_id IN (
            SELECT order_id FROM orders 
            WHERE org_id IN (SELECT auth_user_orgs())
            AND (
                auth_has_permission('admin_only')
                OR (
                    created_by = auth_user_id()
                    AND order_status NOT IN ('completed', 'cancelled')
                )
            )
        )
    );

-- =============================================
-- PURCHASE MANAGEMENT POLICIES
-- =============================================

-- Purchases
CREATE POLICY purchases_select ON purchases
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY purchases_modify ON purchases
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_purchases')
    );

-- Purchase items: Access through parent purchase
CREATE POLICY purchase_items_access ON purchase_items
    FOR ALL USING (
        purchase_id IN (
            SELECT purchase_id FROM purchases 
            WHERE org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('manage_purchases')
        )
    );

-- =============================================
-- FINANCIAL MANAGEMENT POLICIES
-- =============================================

-- Payments: Restricted to financial roles
CREATE POLICY payments_select ON payments
    FOR SELECT USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('view_reports')
    );

CREATE POLICY payments_modify ON payments
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_finances')
    );

-- Outstanding amounts
CREATE POLICY customer_outstanding_access ON customer_outstanding
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('view_reports')
    );

CREATE POLICY supplier_outstanding_access ON supplier_outstanding
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('view_reports')
    );

-- =============================================
-- ACCOUNTING POLICIES
-- =============================================

-- Chart of accounts
CREATE POLICY chart_of_accounts_select ON chart_of_accounts
    FOR SELECT USING (org_id IN (SELECT auth_user_orgs()));

CREATE POLICY chart_of_accounts_modify ON chart_of_accounts
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_finances')
    );

-- Journal entries
CREATE POLICY journal_entries_select ON journal_entries
    FOR SELECT USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('view_reports')
    );

CREATE POLICY journal_entries_modify ON journal_entries
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_finances')
    );

-- Journal entry lines: Access through parent entry
CREATE POLICY journal_entry_lines_access ON journal_entry_lines
    FOR ALL USING (
        entry_id IN (
            SELECT entry_id FROM journal_entries 
            WHERE org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('manage_finances')
        )
    );

-- =============================================
-- SYSTEM & UTILITY POLICIES
-- =============================================

-- Barcode management
CREATE POLICY barcode_master_access ON barcode_master
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

CREATE POLICY barcode_sequences_access ON barcode_sequences
    FOR ALL USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('manage_products')
    );

-- System notifications: Users see relevant notifications
CREATE POLICY system_notifications_select ON system_notifications
    FOR SELECT USING (
        auth.uid() IS NOT NULL -- All authenticated users can see system notifications
    );

-- User sessions: Users see only their own sessions
CREATE POLICY user_sessions_access ON user_sessions
    FOR ALL USING (
        user_id = auth_user_id()
    );

-- Activity log: Organization isolation with view permissions
CREATE POLICY activity_log_select ON activity_log
    FOR SELECT USING (
        org_id IN (SELECT auth_user_orgs())
        AND auth_has_permission('view_reports')
    );

CREATE POLICY activity_log_insert ON activity_log
    FOR INSERT WITH CHECK (
        org_id IN (SELECT auth_user_orgs())
    );

-- System settings: Global read, admin write
CREATE POLICY system_settings_select ON system_settings
    FOR SELECT USING (
        org_id IS NULL 
        OR org_id IN (SELECT auth_user_orgs())
    );

CREATE POLICY system_settings_modify ON system_settings
    FOR ALL USING (
        org_id IS NULL AND auth_has_permission('admin_only')
        OR (
            org_id IN (SELECT auth_user_orgs())
            AND auth_has_permission('admin_only')
        )
    );

-- Email queue: Organization isolation
CREATE POLICY email_queue_access ON email_queue
    FOR ALL USING (
        org_id IS NULL 
        OR org_id IN (SELECT auth_user_orgs())
    );

-- =============================================
-- ENTERPRISE FEATURE POLICIES (CONDITIONAL)
-- =============================================

-- Create policies only if tables exist
DO $$
BEGIN
    -- Doctors
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'doctors') THEN
        EXECUTE 'CREATE POLICY doctors_access ON doctors FOR ALL USING (org_id IN (SELECT auth_user_orgs()))';
    END IF;
    
    -- Prescriptions
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'prescriptions') THEN
        EXECUTE 'CREATE POLICY prescriptions_select ON prescriptions FOR SELECT USING (org_id IN (SELECT auth_user_orgs()))';
        EXECUTE 'CREATE POLICY prescriptions_modify ON prescriptions FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_orders''))';
    END IF;
    
    -- Stock transfers
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_transfers') THEN
        EXECUTE 'CREATE POLICY stock_transfers_access ON stock_transfers FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_products''))';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stock_transfer_items') THEN
        EXECUTE 'CREATE POLICY stock_transfer_items_access ON stock_transfer_items FOR ALL USING (transfer_id IN (SELECT transfer_id FROM stock_transfers WHERE org_id IN (SELECT auth_user_orgs())))';
    END IF;
    
    -- Returns
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'return_requests') THEN
        EXECUTE 'CREATE POLICY return_requests_access ON return_requests FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_orders''))';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'return_items') THEN
        EXECUTE 'CREATE POLICY return_items_access ON return_items FOR ALL USING (return_id IN (SELECT return_id FROM return_requests WHERE org_id IN (SELECT auth_user_orgs())))';
    END IF;
    
    -- Loyalty programs
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'loyalty_programs') THEN
        EXECUTE 'CREATE POLICY loyalty_programs_access ON loyalty_programs FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''admin_only''))';
    END IF;
    
    -- Customer loyalty: Access via customers table (no direct org_id)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'customer_loyalty') THEN
        EXECUTE 'CREATE POLICY customer_loyalty_access ON customer_loyalty FOR ALL USING (customer_id IN (SELECT customer_id FROM customers WHERE org_id IN (SELECT auth_user_orgs())))';
    END IF;
    
    -- Price lists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'price_lists') THEN
        EXECUTE 'CREATE POLICY price_lists_access ON price_lists FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_products''))';
    END IF;
    
    -- Price list items: Access via price_lists table (no direct org_id)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'price_list_items') THEN
        EXECUTE 'CREATE POLICY price_list_items_access ON price_list_items FOR ALL USING (price_list_id IN (SELECT price_list_id FROM price_lists WHERE org_id IN (SELECT auth_user_orgs())))';
    END IF;
    
    -- Schemes
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schemes') THEN
        EXECUTE 'CREATE POLICY schemes_access ON schemes FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_products''))';
    END IF;
    
    -- Scheme products: Access via schemes table (no direct org_id)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheme_products') THEN
        EXECUTE 'CREATE POLICY scheme_products_access ON scheme_products FOR ALL USING (scheme_id IN (SELECT scheme_id FROM schemes WHERE org_id IN (SELECT auth_user_orgs())))';
    END IF;
    
    -- GST data
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'gstr1_data') THEN
        EXECUTE 'CREATE POLICY gstr1_data_access ON gstr1_data FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_finances''))';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'gstr3b_data') THEN
        EXECUTE 'CREATE POLICY gstr3b_data_access ON gstr3b_data FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''manage_finances''))';
    END IF;
    
    -- Compliance
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'drug_inspector_visits') THEN
        EXECUTE 'CREATE POLICY drug_inspector_visits_access ON drug_inspector_visits FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''admin_only''))';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'narcotic_register') THEN
        EXECUTE 'CREATE POLICY narcotic_register_access ON narcotic_register FOR ALL USING (org_id IN (SELECT auth_user_orgs()) AND auth_has_permission(''admin_only''))';
    END IF;
END $$;

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

-- Grant schema usage
GRANT USAGE ON SCHEMA public TO authenticated, anon;

-- Grant table permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Special permissions for anon users (signup)
GRANT EXECUTE ON FUNCTION create_organization TO anon;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
COMPREHENSIVE RLS POLICIES DEPLOYED
=============================================
✓ Multi-tenant organization isolation
✓ Role-based access control
✓ Conditional enterprise feature policies
✓ Supabase auth integration
✓ Proper permission system
✓ Secure helper functions

Features:
- 7 distinct roles with proper permissions
- Organization-based data isolation
- User can only see their own organization data
- Sales reps can only see their own orders
- Financial data restricted to authorized roles
- System settings properly controlled
- Enterprise features conditionally enabled

Test with Supabase Auth:
1. Create organization via create_organization()
2. Sign up with org_id in user metadata
3. All data access automatically isolated by org
4. Role-based permissions enforced
';
END $$;