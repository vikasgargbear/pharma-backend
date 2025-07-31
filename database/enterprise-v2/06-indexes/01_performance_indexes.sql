-- =============================================
-- PERFORMANCE OPTIMIZATION INDEXES
-- =============================================
-- Comprehensive indexes for optimal query performance
-- across all schemas and tables
-- =============================================

-- =============================================
-- MASTER SCHEMA INDEXES
-- =============================================

-- Organizations
CREATE INDEX idx_organizations_active ON master.organizations(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_organizations_gstin ON master.organizations(gstin);

-- Branches
CREATE INDEX idx_branches_org_active ON master.branches(org_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_branches_type ON master.branches(branch_type, is_active);
CREATE INDEX idx_branches_state ON master.branches USING GIN ((address->>'state'));

-- Product Categories
CREATE INDEX idx_product_categories_parent ON master.product_categories(parent_category_id) WHERE parent_category_id IS NOT NULL;
CREATE INDEX idx_product_categories_active ON master.product_categories(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_product_categories_narcotic ON master.product_categories(requires_narcotic_license) WHERE requires_narcotic_license = TRUE;

-- Pack Configurations
CREATE INDEX idx_pack_configs_active ON master.pack_configurations(is_active) WHERE is_active = TRUE;

-- Units of Measurement
CREATE INDEX idx_uom_type ON master.units_of_measurement(uom_type, is_active);

-- =============================================
-- INVENTORY SCHEMA INDEXES
-- =============================================

-- Products
CREATE INDEX idx_products_org_active ON inventory.products(org_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_category ON inventory.products(category_id, is_active);
CREATE INDEX idx_products_hsn ON inventory.products(hsn_code);
CREATE INDEX idx_products_name_search ON inventory.products USING gin(to_tsvector('english', product_name));
CREATE INDEX idx_products_generic_search ON inventory.products USING gin(to_tsvector('english', generic_name));
CREATE INDEX idx_products_reorder ON inventory.products(org_id, reorder_level) WHERE reorder_level IS NOT NULL AND is_active = TRUE;

-- Batches
CREATE INDEX idx_batches_product_active ON inventory.batches(product_id, batch_status) WHERE batch_status = 'active';
CREATE INDEX idx_batches_expiry ON inventory.batches(expiry_date, batch_status) WHERE batch_status = 'active';
CREATE INDEX idx_batches_supplier ON inventory.batches(supplier_id);
CREATE INDEX idx_batches_quantity ON inventory.batches(product_id, quantity_available) WHERE quantity_available > 0;
CREATE INDEX idx_batches_narcotic ON inventory.batches(product_id, narcotic_balance) WHERE narcotic_balance IS NOT NULL;

-- Storage Locations
CREATE INDEX idx_storage_locations_branch ON inventory.storage_locations(branch_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_storage_locations_type ON inventory.storage_locations(location_type, is_active);
CREATE INDEX idx_storage_locations_sales ON inventory.storage_locations(branch_id, is_sales_location) WHERE is_sales_location = TRUE;

-- Location Wise Stock
CREATE INDEX idx_location_stock_product ON inventory.location_wise_stock(product_id, location_id);
CREATE INDEX idx_location_stock_batch ON inventory.location_wise_stock(batch_id, location_id);
CREATE INDEX idx_location_stock_available ON inventory.location_wise_stock(product_id, quantity_available) WHERE quantity_available > 0;
CREATE INDEX idx_location_stock_movement ON inventory.location_wise_stock(last_movement_date);
CREATE INDEX idx_location_stock_status ON inventory.location_wise_stock(stock_status, product_id);

-- Inventory Movements
CREATE INDEX idx_inventory_movements_date ON inventory.inventory_movements(movement_date, movement_type);
CREATE INDEX idx_inventory_movements_product ON inventory.inventory_movements(product_id, movement_date);
CREATE INDEX idx_inventory_movements_batch ON inventory.inventory_movements(batch_id);
CREATE INDEX idx_inventory_movements_reference ON inventory.inventory_movements(reference_type, reference_id);
CREATE INDEX idx_inventory_movements_location ON inventory.inventory_movements(location_id, movement_date);

-- Stock Reservations
CREATE INDEX idx_stock_reservations_active ON inventory.stock_reservations(reservation_status, expires_at) WHERE reservation_status = 'active';
CREATE INDEX idx_stock_reservations_product ON inventory.stock_reservations(product_id, reservation_status);
CREATE INDEX idx_stock_reservations_reference ON inventory.stock_reservations(reference_type, reference_id);

-- Stock Adjustments
CREATE INDEX idx_stock_adjustments_date ON inventory.stock_adjustments(adjustment_date, adjustment_type);
CREATE INDEX idx_stock_adjustments_status ON inventory.stock_adjustments(approval_status) WHERE approval_status = 'pending';

-- =============================================
-- PARTIES SCHEMA INDEXES
-- =============================================

-- Customers
CREATE INDEX idx_customers_org_active ON parties.customers(org_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_customers_name_search ON parties.customers USING gin(to_tsvector('english', customer_name));
CREATE INDEX idx_customers_gstin ON parties.customers(gstin) WHERE gstin IS NOT NULL;
CREATE INDEX idx_customers_phone ON parties.customers(primary_phone);
CREATE INDEX idx_customers_category ON parties.customers(category_id);
CREATE INDEX idx_customers_credit ON parties.customers((credit_info->>'credit_limit')) WHERE credit_info->>'credit_limit' IS NOT NULL;

-- Suppliers
CREATE INDEX idx_suppliers_org_active ON parties.suppliers(org_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_suppliers_name_search ON parties.suppliers USING gin(to_tsvector('english', supplier_name));
CREATE INDEX idx_suppliers_gstin ON parties.suppliers(gstin) WHERE gstin IS NOT NULL;
CREATE INDEX idx_suppliers_category ON parties.suppliers(supplier_category);

-- Customer Categories
CREATE INDEX idx_customer_categories_active ON parties.customer_categories(is_active) WHERE is_active = TRUE;

-- Customer Outstanding
CREATE INDEX idx_customer_outstanding_customer ON parties.customer_outstanding(customer_id, status) WHERE status IN ('open', 'partial');
CREATE INDEX idx_customer_outstanding_due ON parties.customer_outstanding(due_date, status) WHERE status IN ('open', 'partial');
CREATE INDEX idx_customer_outstanding_aging ON parties.customer_outstanding(days_overdue, status);

-- =============================================
-- SALES SCHEMA INDEXES
-- =============================================

-- Orders
CREATE INDEX idx_orders_org_date ON sales.orders(org_id, order_date);
CREATE INDEX idx_orders_customer ON sales.orders(customer_id, order_date);
CREATE INDEX idx_orders_status ON sales.orders(order_status, order_date);
CREATE INDEX idx_orders_branch ON sales.orders(branch_id, order_date);
CREATE INDEX idx_orders_fulfillment ON sales.orders(fulfillment_status) WHERE fulfillment_status != 'fulfilled';
CREATE INDEX idx_orders_salesperson ON sales.orders(salesperson_id, order_date);

-- Order Items
CREATE INDEX idx_order_items_order ON sales.order_items(order_id);
CREATE INDEX idx_order_items_product ON sales.order_items(product_id);
CREATE INDEX idx_order_items_delivery ON sales.order_items(delivery_status) WHERE delivery_status != 'delivered';

-- Invoices
CREATE INDEX idx_invoices_org_date ON sales.invoices(org_id, invoice_date);
CREATE INDEX idx_invoices_customer ON sales.invoices(customer_id, invoice_date);
CREATE INDEX idx_invoices_status ON sales.invoices(invoice_status, invoice_date);
CREATE INDEX idx_invoices_number ON sales.invoices(invoice_number);
CREATE INDEX idx_invoices_order ON sales.invoices(order_id) WHERE order_id IS NOT NULL;
CREATE INDEX idx_invoices_due ON sales.invoices(due_date, invoice_status) WHERE invoice_status = 'posted';
CREATE INDEX idx_invoices_branch ON sales.invoices(branch_id, invoice_date);

-- Invoice Items
CREATE INDEX idx_invoice_items_invoice ON sales.invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_product ON sales.invoice_items(product_id);
CREATE INDEX idx_invoice_items_batch_alloc ON sales.invoice_items USING GIN(batch_allocation);

-- Sales Returns
CREATE INDEX idx_sales_returns_invoice ON sales.sales_returns(invoice_id);
CREATE INDEX idx_sales_returns_customer ON sales.sales_returns(customer_id, return_date);
CREATE INDEX idx_sales_returns_status ON sales.sales_returns(approval_status) WHERE approval_status = 'pending';
CREATE INDEX idx_sales_returns_credit_note ON sales.sales_returns(credit_note_status) WHERE credit_note_status = 'pending';

-- Price Lists
CREATE INDEX idx_price_lists_active ON sales.price_lists(is_active, valid_from, valid_to) WHERE is_active = TRUE;
CREATE INDEX idx_price_lists_branch ON sales.price_lists(branch_id, is_active);

-- Price List Items
CREATE INDEX idx_price_list_items_list ON sales.price_list_items(price_list_id, is_active);
CREATE INDEX idx_price_list_items_product ON sales.price_list_items(product_id, is_active);
CREATE INDEX idx_price_list_items_category ON sales.price_list_items(customer_category_id, product_id);

-- Sales Schemes
CREATE INDEX idx_sales_schemes_active ON sales.sales_schemes(is_active, valid_from, valid_to) WHERE is_active = TRUE;
CREATE INDEX idx_sales_schemes_products ON sales.sales_schemes USING GIN(applicable_products);
CREATE INDEX idx_sales_schemes_branches ON sales.sales_schemes USING GIN(branches);

-- =============================================
-- PROCUREMENT SCHEMA INDEXES
-- =============================================

-- Purchase Orders
CREATE INDEX idx_po_org_date ON procurement.purchase_orders(org_id, po_date);
CREATE INDEX idx_po_supplier ON procurement.purchase_orders(supplier_id, po_date);
CREATE INDEX idx_po_status ON procurement.purchase_orders(po_status, po_date);
CREATE INDEX idx_po_number ON procurement.purchase_orders(po_number);
CREATE INDEX idx_po_branch ON procurement.purchase_orders(branch_id, po_date);

-- Purchase Order Items
CREATE INDEX idx_po_items_po ON procurement.purchase_order_items(po_id);
CREATE INDEX idx_po_items_product ON procurement.purchase_order_items(product_id);
CREATE INDEX idx_po_items_pending ON procurement.purchase_order_items(po_id, quantity_received) WHERE quantity_ordered > COALESCE(quantity_received, 0);

-- GRN
CREATE INDEX idx_grn_org_date ON procurement.goods_receipt_notes(org_id, grn_date);
CREATE INDEX idx_grn_po ON procurement.goods_receipt_notes(po_id);
CREATE INDEX idx_grn_supplier ON procurement.goods_receipt_notes(supplier_id, grn_date);
CREATE INDEX idx_grn_status ON procurement.goods_receipt_notes(grn_status) WHERE grn_status = 'pending_approval';
CREATE INDEX idx_grn_number ON procurement.goods_receipt_notes(grn_number);

-- GRN Items
CREATE INDEX idx_grn_items_grn ON procurement.grn_items(grn_id);
CREATE INDEX idx_grn_items_product ON procurement.grn_items(product_id);
CREATE INDEX idx_grn_items_batch ON procurement.grn_items(batch_number, product_id);

-- Supplier Invoices
CREATE INDEX idx_supplier_invoices_supplier ON procurement.supplier_invoices(supplier_id, invoice_date);
CREATE INDEX idx_supplier_invoices_grn ON procurement.supplier_invoices(grn_id);
CREATE INDEX idx_supplier_invoices_status ON procurement.supplier_invoices(invoice_status, due_date);
CREATE INDEX idx_supplier_invoices_due ON procurement.supplier_invoices(due_date, invoice_status) WHERE invoice_status = 'posted';

-- Purchase Requisitions
CREATE INDEX idx_requisitions_branch ON procurement.purchase_requisitions(branch_id, requisition_date);
CREATE INDEX idx_requisitions_status ON procurement.purchase_requisitions(requisition_status) WHERE requisition_status IN ('draft', 'pending_approval');

-- Supplier Products
CREATE INDEX idx_supplier_products_product ON procurement.supplier_products(product_id, is_preferred);
CREATE INDEX idx_supplier_products_supplier ON procurement.supplier_products(supplier_id, is_active);

-- =============================================
-- FINANCIAL SCHEMA INDEXES
-- =============================================

-- Journal Entries
CREATE INDEX idx_journal_entries_date ON financial.journal_entries(entry_date, org_id);
CREATE INDEX idx_journal_entries_status ON financial.journal_entries(posting_status) WHERE posting_status = 'draft';
CREATE INDEX idx_journal_entries_number ON financial.journal_entries(entry_number);
CREATE INDEX idx_journal_entries_reference ON financial.journal_entries(reference_type, reference_id);

-- Journal Entry Lines
CREATE INDEX idx_journal_lines_entry ON financial.journal_entry_lines(entry_id);
CREATE INDEX idx_journal_lines_account ON financial.journal_entry_lines(account_id);

-- Payments
CREATE INDEX idx_payments_org_date ON financial.payments(org_id, payment_date);
CREATE INDEX idx_payments_party ON financial.payments(party_type, party_id, payment_date);
CREATE INDEX idx_payments_status ON financial.payments(payment_status, payment_date);
CREATE INDEX idx_payments_reference ON financial.payments(reference_type, reference_id);
CREATE INDEX idx_payments_mode ON financial.payments(payment_mode, payment_status);
CREATE INDEX idx_payments_allocation ON financial.payments(allocation_status) WHERE allocation_status != 'full';

-- Payment Allocations
CREATE INDEX idx_payment_allocations_payment ON financial.payment_allocations(payment_id);
CREATE INDEX idx_payment_allocations_reference ON financial.payment_allocations(reference_type, reference_id);

-- PDC Management
CREATE INDEX idx_pdc_maturity ON financial.pdc_management(maturity_date, pdc_status) WHERE pdc_status = 'pending';
CREATE INDEX idx_pdc_party ON financial.pdc_management(party_type, party_id);
CREATE INDEX idx_pdc_status ON financial.pdc_management(pdc_status) WHERE pdc_status != 'cleared';

-- Customer Outstanding
CREATE INDEX idx_fin_customer_outstanding ON financial.customer_outstanding(customer_id, status) WHERE status IN ('open', 'partial');
CREATE INDEX idx_fin_outstanding_due ON financial.customer_outstanding(due_date, status);
CREATE INDEX idx_fin_outstanding_aging ON financial.customer_outstanding(aging_bucket, status);

-- Supplier Outstanding
CREATE INDEX idx_supplier_outstanding ON financial.supplier_outstanding(supplier_id, status) WHERE status IN ('open', 'partial');
CREATE INDEX idx_supplier_outstanding_due ON financial.supplier_outstanding(due_date, status);

-- =============================================
-- GST SCHEMA INDEXES
-- =============================================

-- GSTR1 Data
CREATE INDEX idx_gstr1_period ON gst.gstr1_data(org_id, return_period, filing_status);
CREATE INDEX idx_gstr1_invoice ON gst.gstr1_data(invoice_id);

-- GSTR2A Data
CREATE INDEX idx_gstr2a_period ON gst.gstr2a_data(org_id, return_period);
CREATE INDEX idx_gstr2a_supplier ON gst.gstr2a_data(supplier_gstin, invoice_number);

-- GSTR3B Summary
CREATE INDEX idx_gstr3b_period ON gst.gstr3b_summary(org_id, return_period, filing_status);

-- GST Returns
CREATE INDEX idx_gst_returns_period ON gst.gst_returns(org_id, return_type, return_period);
CREATE INDEX idx_gst_returns_status ON gst.gst_returns(filing_status) WHERE filing_status IN ('pending', 'draft');

-- E-way Bills
CREATE INDEX idx_eway_bills_invoice ON gst.eway_bills(invoice_id);
CREATE INDEX idx_eway_bills_status ON gst.eway_bills(eway_bill_status) WHERE eway_bill_status = 'active';
CREATE INDEX idx_eway_bills_validity ON gst.eway_bills(valid_until) WHERE eway_bill_status = 'active';

-- =============================================
-- COMPLIANCE SCHEMA INDEXES
-- =============================================

-- Business Licenses
CREATE INDEX idx_licenses_org_expiry ON compliance.business_licenses(org_id, expiry_date) WHERE is_active = TRUE;
CREATE INDEX idx_licenses_type ON compliance.business_licenses(license_type, expiry_date);
CREATE INDEX idx_licenses_branches ON compliance.business_licenses USING GIN(applicable_branches);

-- Narcotic Drug Register
CREATE INDEX idx_narcotic_register_product ON compliance.narcotic_drug_register(product_id, batch_id, register_date);
CREATE INDEX idx_narcotic_register_date ON compliance.narcotic_drug_register(register_date, transaction_type);
CREATE INDEX idx_narcotic_register_verification ON compliance.narcotic_drug_register(verification_status) WHERE verification_status = 'pending_verification';

-- Regulatory Inspections
CREATE INDEX idx_inspections_org_date ON compliance.regulatory_inspections(org_id, inspection_date);
CREATE INDEX idx_inspections_status ON compliance.regulatory_inspections(inspection_status) WHERE inspection_status != 'closed';

-- Inspection Findings
CREATE INDEX idx_inspection_findings ON compliance.inspection_findings(inspection_id, severity, status);
CREATE INDEX idx_findings_closure ON compliance.inspection_findings(target_closure_date, status) WHERE status != 'closed';

-- Quality Deviations
CREATE INDEX idx_deviations_date ON compliance.quality_deviations(deviation_date, severity);
CREATE INDEX idx_deviations_product ON compliance.quality_deviations(product_id, batch_id);
CREATE INDEX idx_deviations_status ON compliance.quality_deviations(deviation_status) WHERE deviation_status != 'closed';

-- GxP Audit Log
CREATE INDEX idx_gxp_audit_table ON compliance.gxp_audit_log(table_name, record_id, action_timestamp);
CREATE INDEX idx_gxp_audit_user ON compliance.gxp_audit_log(user_id, action_timestamp);

-- =============================================
-- ANALYTICS SCHEMA INDEXES
-- =============================================

-- KPI Metrics
CREATE INDEX idx_kpi_metrics_date ON analytics.kpi_metrics(metric_date, kpi_name);
CREATE INDEX idx_kpi_metrics_org ON analytics.kpi_metrics(org_id, kpi_name, metric_date);

-- Sales Analytics
CREATE INDEX idx_sales_analytics_date ON analytics.sales_analytics(analysis_date, org_id);
CREATE INDEX idx_sales_analytics_customer ON analytics.sales_analytics(customer_id, analysis_date);
CREATE INDEX idx_sales_analytics_product ON analytics.sales_analytics(product_id, analysis_date);

-- Inventory Analytics
CREATE INDEX idx_inventory_analytics_date ON analytics.inventory_analytics(analysis_date, org_id);
CREATE INDEX idx_inventory_analytics_product ON analytics.inventory_analytics(product_id, analysis_date);

-- Customer Behavior
CREATE INDEX idx_customer_behavior ON analytics.customer_behavior(customer_id, analysis_date);
CREATE INDEX idx_customer_rfm ON analytics.customer_behavior(rfm_segment, org_id);

-- Product Performance
CREATE INDEX idx_product_performance_date ON analytics.product_performance(analysis_date, product_id);
CREATE INDEX idx_product_performance_category ON analytics.product_performance(category_id, analysis_date);

-- =============================================
-- SYSTEM_CONFIG SCHEMA INDEXES
-- =============================================

-- Users
CREATE INDEX idx_users_username ON system_config.users(username) WHERE is_active = TRUE;
CREATE INDEX idx_users_email ON system_config.users(email) WHERE is_active = TRUE;

-- User Sessions
CREATE INDEX idx_user_sessions_active ON system_config.user_sessions(user_id, expires_at) WHERE expires_at > CURRENT_TIMESTAMP;
CREATE INDEX idx_user_sessions_token ON system_config.user_sessions(session_token) WHERE expires_at > CURRENT_TIMESTAMP;

-- User Roles
CREATE INDEX idx_user_roles ON system_config.user_roles(user_id, role_id);
CREATE INDEX idx_user_roles_role ON system_config.user_roles(role_id);

-- System Notifications
CREATE INDEX idx_system_notifications_created ON system_config.system_notifications(created_at, notification_type);
CREATE INDEX idx_system_notifications_priority ON system_config.system_notifications(priority, created_at) WHERE priority IN ('critical', 'high');

-- User Notifications
CREATE INDEX idx_user_notifications_unread ON system_config.user_notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX idx_user_notifications_delivery ON system_config.user_notifications(delivery_status, created_at);

-- Audit Log
CREATE INDEX idx_audit_log_user_date ON system_config.audit_log(user_id, created_at);
CREATE INDEX idx_audit_log_table ON system_config.audit_log(table_name, action, created_at);

-- System Settings
CREATE INDEX idx_system_settings_org ON system_config.system_settings(org_id, setting_key);

-- =============================================
-- FULL TEXT SEARCH INDEXES
-- =============================================

-- Product search
CREATE INDEX idx_products_full_text ON inventory.products 
USING gin(
    to_tsvector('english', 
        COALESCE(product_name, '') || ' ' || 
        COALESCE(generic_name, '') || ' ' || 
        COALESCE(manufacturer, '') || ' ' ||
        COALESCE(product_description, '')
    )
);

-- Customer search
CREATE INDEX idx_customers_full_text ON parties.customers 
USING gin(
    to_tsvector('english', 
        COALESCE(customer_name, '') || ' ' || 
        COALESCE(contact_person, '') || ' ' ||
        COALESCE(address->>'city', '')
    )
);

-- Supplier search
CREATE INDEX idx_suppliers_full_text ON parties.suppliers 
USING gin(
    to_tsvector('english', 
        COALESCE(supplier_name, '') || ' ' || 
        COALESCE(contact_person, '') || ' ' ||
        COALESCE(address->>'city', '')
    )
);

-- =============================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =============================================

-- Invoice with customer and date
CREATE INDEX idx_invoices_customer_date_status ON sales.invoices(customer_id, invoice_date, invoice_status);

-- Stock by product and location
CREATE INDEX idx_stock_product_location_available ON inventory.location_wise_stock(product_id, location_id, quantity_available);

-- Outstanding by customer and age
CREATE INDEX idx_outstanding_customer_age ON financial.customer_outstanding(customer_id, days_overdue, outstanding_amount);

-- Orders pending fulfillment
CREATE INDEX idx_orders_pending_fulfillment ON sales.orders(branch_id, fulfillment_status, order_date) 
WHERE fulfillment_status IN ('pending', 'partial');

-- Expiring batches
CREATE INDEX idx_batches_expiring ON inventory.batches(expiry_date, product_id, quantity_available) 
WHERE batch_status = 'active' AND quantity_available > 0;

-- =============================================
-- PERFORMANCE MONITORING
-- =============================================

-- Create extension for monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Function to analyze index usage
CREATE OR REPLACE FUNCTION analyze_index_usage()
RETURNS TABLE (
    schemaname TEXT,
    tablename TEXT,
    indexname TEXT,
    index_size TEXT,
    times_used BIGINT,
    usage_ratio NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname,
        s.tablename,
        s.indexname,
        pg_size_pretty(pg_relation_size(s.indexrelid)) as index_size,
        COALESCE(i.idx_scan, 0) as times_used,
        ROUND(
            CASE 
                WHEN t.seq_scan + t.idx_scan > 0 
                THEN 100.0 * i.idx_scan / (t.seq_scan + t.idx_scan)
                ELSE 0
            END, 2
        ) as usage_ratio
    FROM pg_stat_user_indexes i
    JOIN pg_indexes s ON i.indexrelname = s.indexname AND i.schemaname = s.schemaname
    JOIN pg_stat_user_tables t ON i.tablename = t.tablename AND i.schemaname = t.schemaname
    WHERE s.schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY s.schemaname, s.tablename, s.indexname;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- MAINTENANCE RECOMMENDATIONS
-- =============================================
COMMENT ON FUNCTION analyze_index_usage() IS 'Analyze index usage to identify unused or rarely used indexes';

/*
Maintenance Schedule:
1. Run ANALYZE weekly on all tables
2. Run VACUUM ANALYZE monthly on high-transaction tables
3. Review index usage quarterly using analyze_index_usage()
4. Rebuild indexes annually or when fragmentation > 30%

High-Priority Tables for Maintenance:
- inventory.inventory_movements
- sales.invoices
- sales.invoice_items
- financial.journal_entry_lines
- inventory.location_wise_stock
*/