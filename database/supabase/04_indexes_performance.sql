-- =============================================
-- PHARMACEUTICAL ERP - INDEXES & PERFORMANCE
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Database indexes for optimal performance
-- Deploy Order: 4th - After triggers
-- =============================================

-- =============================================
-- MULTI-TENANT ISOLATION INDEXES
-- =============================================

-- Core organization isolation
CREATE INDEX IF NOT EXISTS idx_customers_org_id ON customers(org_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_org_id ON suppliers(org_id);
CREATE INDEX IF NOT EXISTS idx_products_org_id ON products(org_id);
CREATE INDEX IF NOT EXISTS idx_batches_org_id ON batches(org_id);
CREATE INDEX IF NOT EXISTS idx_orders_org_id ON orders(org_id);
CREATE INDEX IF NOT EXISTS idx_payments_org_id ON payments(org_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_org_id ON inventory_movements(org_id);
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_org_id ON customer_outstanding(org_id);

-- =============================================
-- BUSINESS QUERY INDEXES
-- =============================================

-- Product search and filtering
CREATE INDEX IF NOT EXISTS idx_products_org_name ON products(org_id, product_name);
CREATE INDEX IF NOT EXISTS idx_products_org_category ON products(org_id, category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_org_manufacturer ON products(org_id, manufacturer) WHERE manufacturer IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_hsn_code ON products(hsn_code) WHERE hsn_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_search_keywords ON products USING GIN(search_keywords);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(org_id, is_discontinued);

-- Product type and UOM indexes
CREATE INDEX IF NOT EXISTS idx_product_types_org ON product_types(COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::UUID));
CREATE INDEX IF NOT EXISTS idx_units_of_measure_org ON units_of_measure(COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::UUID));
CREATE INDEX IF NOT EXISTS idx_product_uom_conversions_product ON product_uom_conversions(product_id, from_uom_code, to_uom_code);

-- Batch management (FEFO optimization)
CREATE INDEX IF NOT EXISTS idx_batches_fefo ON batches(org_id, product_id, expiry_date, quantity_available) WHERE quantity_available > 0;
CREATE INDEX IF NOT EXISTS idx_batches_product_status ON batches(product_id, batch_status, is_blocked) WHERE quantity_available > 0;
CREATE INDEX IF NOT EXISTS idx_batches_expiry_near ON batches(org_id, expiry_date) WHERE is_near_expiry = TRUE;
CREATE INDEX IF NOT EXISTS idx_batches_branch_product ON batches(branch_id, product_id) WHERE branch_id IS NOT NULL;

-- Customer and supplier lookups
CREATE INDEX IF NOT EXISTS idx_customers_org_name ON customers(org_id, customer_name);
CREATE INDEX IF NOT EXISTS idx_customers_org_code ON customers(org_id, customer_code);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone) WHERE phone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_gst ON customers(gst_number) WHERE gst_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(org_id, is_active);

CREATE INDEX IF NOT EXISTS idx_suppliers_org_name ON suppliers(org_id, supplier_name);
CREATE INDEX IF NOT EXISTS idx_suppliers_org_code ON suppliers(org_id, supplier_code);
CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(org_id, is_active);

-- =============================================
-- ORDER & TRANSACTION INDEXES
-- =============================================

-- Order management
CREATE INDEX IF NOT EXISTS idx_orders_org_date ON orders(org_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_org_status ON orders(org_id, order_status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX IF NOT EXISTS idx_orders_org_number ON orders(org_id, order_number);
CREATE INDEX IF NOT EXISTS idx_orders_invoice_number ON orders(invoice_number) WHERE invoice_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_payment_mode ON orders(org_id, payment_mode);

-- Order items for reporting
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_batch ON order_items(batch_id) WHERE batch_id IS NOT NULL;

-- Purchase management
CREATE INDEX IF NOT EXISTS idx_purchases_org_date ON purchases(org_id, purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchases_supplier_date ON purchases(supplier_id, purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchases_org_status ON purchases(org_id, purchase_status);

CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_purchase_items_product ON purchase_items(product_id);

-- =============================================
-- PAYMENT & OUTSTANDING INDEXES
-- =============================================

-- Payment processing
CREATE INDEX IF NOT EXISTS idx_payments_org_date ON payments(org_id, payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_customer_date ON payments(customer_id, payment_date);
CREATE INDEX IF NOT EXISTS idx_payments_org_status ON payments(org_id, payment_status);
CREATE INDEX IF NOT EXISTS idx_payments_org_mode ON payments(org_id, payment_mode);
CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference_number) WHERE reference_number IS NOT NULL;

-- Outstanding management
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_org_status ON customer_outstanding(org_id, status);
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_customer_status ON customer_outstanding(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_due_date ON customer_outstanding(due_date) WHERE status IN ('pending', 'overdue');
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_invoice_date ON customer_outstanding(invoice_date);
CREATE INDEX IF NOT EXISTS idx_customer_outstanding_amount ON customer_outstanding(org_id, outstanding_amount) WHERE outstanding_amount > 0;

-- =============================================
-- INVENTORY & MOVEMENTS INDEXES
-- =============================================

-- Inventory movements tracking
CREATE INDEX IF NOT EXISTS idx_inventory_movements_org_date ON inventory_movements(org_id, movement_date);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_product_date ON inventory_movements(product_id, movement_date);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_batch ON inventory_movements(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_inventory_movements_reference ON inventory_movements(reference_type, reference_id) WHERE reference_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_inventory_movements_type ON inventory_movements(org_id, movement_type);

-- =============================================
-- USER & ORGANIZATION INDEXES
-- =============================================

-- User management
CREATE INDEX IF NOT EXISTS idx_org_users_org_email ON org_users(org_id, email);
CREATE INDEX IF NOT EXISTS idx_org_users_org_role ON org_users(org_id, role);
CREATE INDEX IF NOT EXISTS idx_org_users_active ON org_users(org_id, is_active);
CREATE INDEX IF NOT EXISTS idx_org_users_last_login ON org_users(last_login_at) WHERE last_login_at IS NOT NULL;

-- Branch management
CREATE INDEX IF NOT EXISTS idx_org_branches_org_code ON org_branches(org_id, branch_code);
CREATE INDEX IF NOT EXISTS idx_org_branches_active ON org_branches(org_id, is_active);

-- =============================================
-- NOTIFICATION & SYSTEM INDEXES
-- =============================================

-- System notifications
CREATE INDEX IF NOT EXISTS idx_system_notifications_target ON system_notifications(target_type, target_value);
CREATE INDEX IF NOT EXISTS idx_system_notifications_priority ON system_notifications(priority, created_at) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_system_notifications_unread ON system_notifications(created_at) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_system_notifications_expires ON system_notifications(expires_at) WHERE expires_at IS NOT NULL;

-- =============================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =============================================

-- Dashboard queries
CREATE INDEX IF NOT EXISTS idx_orders_monthly_sales ON orders(org_id, order_date, order_status, final_amount) 
WHERE order_status IN ('delivered', 'invoiced');

CREATE INDEX IF NOT EXISTS idx_batches_low_stock ON batches(org_id, product_id, quantity_available) 
WHERE quantity_available > 0;

-- Customer analysis
CREATE INDEX IF NOT EXISTS idx_customers_business_metrics ON customers(org_id, total_business, last_order_date) 
WHERE is_active = TRUE;

-- Product performance
CREATE INDEX IF NOT EXISTS idx_order_items_product_performance ON order_items(product_id, quantity, total_price);

-- Expiry management
CREATE INDEX IF NOT EXISTS idx_batches_expiry_management ON batches(org_id, expiry_date, quantity_available, batch_status) 
WHERE quantity_available > 0 AND batch_status = 'active';

-- =============================================
-- PARTIAL INDEXES FOR OPTIMIZATION
-- =============================================

-- Only index active/non-deleted records
CREATE INDEX IF NOT EXISTS idx_products_active_search ON products(org_id, product_name, category) 
WHERE is_discontinued = FALSE;

CREATE INDEX IF NOT EXISTS idx_customers_active_business ON customers(org_id, customer_name, total_business) 
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_suppliers_active_lookup ON suppliers(org_id, supplier_name) 
WHERE is_active = TRUE;

-- Only index non-zero outstanding amounts
CREATE INDEX IF NOT EXISTS idx_outstanding_pending_amounts ON customer_outstanding(customer_id, outstanding_amount, due_date) 
WHERE status IN ('pending', 'overdue') AND outstanding_amount > 0;

-- Only index available inventory
CREATE INDEX IF NOT EXISTS idx_batches_available_inventory ON batches(product_id, quantity_available, expiry_date) 
WHERE quantity_available > 0 AND batch_status = 'active';

-- =============================================
-- STATISTICS & MAINTENANCE
-- =============================================

-- Update table statistics for better query planning
ANALYZE organizations;
ANALYZE org_users;
ANALYZE org_branches;
ANALYZE products;
ANALYZE product_types;
ANALYZE units_of_measure;
ANALYZE product_uom_conversions;
ANALYZE customers;
ANALYZE suppliers;
ANALYZE batches;
ANALYZE orders;
ANALYZE order_items;
ANALYZE purchases;
ANALYZE purchase_items;
ANALYZE payments;
ANALYZE customer_outstanding;
ANALYZE inventory_movements;
ANALYZE system_notifications;

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
INDEXES & PERFORMANCE OPTIMIZATIONS DEPLOYED
=============================================
✓ Multi-tenant isolation indexes
✓ Business query indexes
✓ Order & transaction indexes
✓ Payment & outstanding indexes
✓ Inventory & movement indexes
✓ User & organization indexes
✓ Notification & system indexes
✓ Composite indexes for complex queries
✓ Partial indexes for optimization
✓ Table statistics updated

Next: Deploy 05_security_rls.sql
';
END $$;