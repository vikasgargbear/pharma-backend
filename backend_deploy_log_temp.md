🚀 Enterprise Pharma Backend - Complete Deployment
==================================================

📊 Target database: postgresql://postgres:I5ejcC77brqe4EPY@db.jfrairkk...

Do you want to reset the database first? (y/n)
⚠️  WARNING: This will delete ALL data!
y
Resetting database...
psql:reset-database.sql:5: NOTICE:  drop cascades to 219 other objects
DETAIL:  drop cascades to table master.organizations
drop cascades to constraint product_categories_org_id_fkey on table inventory.product_categories
drop cascades to constraint units_of_measure_org_id_fkey on table inventory.units_of_measure
drop cascades to constraint products_org_id_fkey on table inventory.products
drop cascades to constraint storage_locations_org_id_fkey on table inventory.storage_locations
drop cascades to constraint stock_transfers_org_id_fkey on table inventory.stock_transfers
drop cascades to constraint customers_org_id_fkey on table parties.customers
drop cascades to constraint suppliers_org_id_fkey on table parties.suppliers
drop cascades to constraint customer_groups_org_id_fkey on table parties.customer_groups
drop cascades to constraint territories_org_id_fkey on table parties.territories
drop cascades to constraint routes_org_id_fkey on table parties.routes
drop cascades to constraint orders_org_id_fkey on table sales.orders
drop cascades to constraint invoices_org_id_fkey on table sales.invoices
drop cascades to constraint delivery_challans_org_id_fkey on table sales.delivery_challans
drop cascades to constraint sales_returns_org_id_fkey on table sales.sales_returns
drop cascades to constraint price_lists_org_id_fkey on table sales.price_lists
drop cascades to constraint sales_schemes_org_id_fkey on table sales.sales_schemes
drop cascades to constraint sales_targets_org_id_fkey on table sales.sales_targets
drop cascades to constraint customer_visits_org_id_fkey on table sales.customer_visits
drop cascades to constraint purchase_orders_org_id_fkey on table procurement.purchase_orders
drop cascades to constraint goods_receipt_notes_org_id_fkey on table procurement.goods_receipt_notes
drop cascades to constraint supplier_invoices_org_id_fkey on table procurement.supplier_invoices
drop cascades to constraint purchase_returns_org_id_fkey on table procurement.purchase_returns
drop cascades to constraint purchase_requisitions_org_id_fkey on table procurement.purchase_requisitions
drop cascades to constraint supplier_quotations_org_id_fkey on table procurement.supplier_quotations
drop cascades to constraint vendor_performance_org_id_fkey on table procurement.vendor_performance
drop cascades to constraint payment_methods_org_id_fkey on table financial.payment_methods
drop cascades to constraint payments_org_id_fkey on table financial.payments
drop cascades to constraint journal_entries_org_id_fkey on table financial.journal_entries
drop cascades to constraint chart_of_accounts_org_id_fkey on table financial.chart_of_accounts
drop cascades to constraint bank_reconciliations_org_id_fkey on table financial.bank_reconciliations
drop cascades to constraint expense_categories_org_id_fkey on table financial.expense_categories
drop cascades to constraint expense_claims_org_id_fkey on table financial.expense_claims
drop cascades to constraint pdc_management_org_id_fkey on table financial.pdc_management
drop cascades to constraint cash_flow_forecast_org_id_fkey on table financial.cash_flow_forecast
drop cascades to constraint gst_rates_org_id_fkey on table gst.gst_rates
drop cascades to constraint gstr1_data_org_id_fkey on table gst.gstr1_data
drop cascades to constraint gstr2a_data_org_id_fkey on table gst.gstr2a_data
drop cascades to constraint gstr2b_data_org_id_fkey on table gst.gstr2b_data
drop cascades to constraint gstr3b_data_org_id_fkey on table gst.gstr3b_data
drop cascades to constraint gst_reconciliation_org_id_fkey on table gst.gst_reconciliation
drop cascades to constraint eway_bills_org_id_fkey on table gst.eway_bills
drop cascades to constraint gst_liability_org_id_fkey on table gst.gst_liability
drop cascades to constraint gst_credit_ledger_org_id_fkey on table gst.gst_credit_ledger
drop cascades to constraint gst_audit_trail_org_id_fkey on table gst.gst_audit_trail
drop cascades to constraint compliance_calendar_org_id_fkey on table gst.compliance_calendar
drop cascades to constraint quality_deviations_org_id_fkey on table compliance.quality_deviations
drop cascades to constraint environmental_compliance_org_id_fkey on table compliance.environmental_compliance
drop cascades to constraint compliance_violations_org_id_fkey on table compliance.compliance_violations
drop cascades to constraint org_compliance_status_org_id_fkey on table compliance.org_compliance_status
drop cascades to constraint report_templates_org_id_fkey on table analytics.report_templates
drop cascades to constraint report_schedules_org_id_fkey on table analytics.report_schedules
drop cascades to constraint report_execution_history_org_id_fkey on table analytics.report_execution_history
drop cascades to constraint dashboards_org_id_fkey on table analytics.dashboards
drop cascades to constraint kpi_definitions_org_id_fkey on table analytics.kpi_definitions
drop cascades to constraint data_quality_metrics_org_id_fkey on table analytics.data_quality_metrics
drop cascades to constraint user_activity_analytics_org_id_fkey on table analytics.user_activity_analytics
drop cascades to constraint alert_definitions_org_id_fkey on table analytics.alert_definitions
drop cascades to constraint audit_logs_org_id_fkey on table system_config.audit_logs
drop cascades to constraint system_notifications_org_id_fkey on table system_config.system_notifications
drop cascades to constraint scheduled_jobs_org_id_fkey on table system_config.scheduled_jobs
drop cascades to constraint system_integrations_org_id_fkey on table system_config.system_integrations
drop cascades to constraint email_templates_org_id_fkey on table system_config.email_templates
drop cascades to constraint scheduled_notifications_org_id_fkey on table system_config.scheduled_notifications
drop cascades to constraint error_logs_org_id_fkey on table system_config.error_logs
drop cascades to constraint batches_org_id_fkey on table inventory.batches
drop cascades to constraint location_wise_stock_org_id_fkey on table inventory.location_wise_stock
drop cascades to constraint stock_reservations_org_id_fkey on table inventory.stock_reservations
drop cascades to constraint inventory_movements_org_id_fkey on table inventory.inventory_movements
drop cascades to constraint reorder_suggestions_org_id_fkey on table inventory.reorder_suggestions
drop cascades to constraint customer_outstanding_org_id_fkey on table financial.customer_outstanding
drop cascades to constraint supplier_outstanding_org_id_fkey on table financial.supplier_outstanding
drop cascades to constraint org_licenses_org_id_fkey on table compliance.org_licenses
drop cascades to constraint regulatory_inspections_org_id_fkey on table compliance.regulatory_inspections
drop cascades to constraint quality_control_tests_org_id_fkey on table compliance.quality_control_tests
drop cascades to constraint system_settings_org_id_fkey on table system_config.system_settings
drop cascades to constraint feature_flags_org_id_fkey on table system_config.feature_flags
drop cascades to table master.org_branches
drop cascades to constraint storage_locations_branch_id_fkey on table inventory.storage_locations
drop cascades to constraint stock_transfers_from_branch_id_fkey on table inventory.stock_transfers
drop cascades to constraint stock_transfers_to_branch_id_fkey on table inventory.stock_transfers
drop cascades to constraint orders_branch_id_fkey on table sales.orders
drop cascades to constraint invoices_branch_id_fkey on table sales.invoices
drop cascades to constraint delivery_challans_branch_id_fkey on table sales.delivery_challans
drop cascades to constraint sales_returns_branch_id_fkey on table sales.sales_returns
drop cascades to constraint purchase_orders_branch_id_fkey on table procurement.purchase_orders
drop cascades to constraint goods_receipt_notes_branch_id_fkey on table procurement.goods_receipt_notes
drop cascades to constraint supplier_invoices_branch_id_fkey on table procurement.supplier_invoices
drop cascades to constraint purchase_returns_branch_id_fkey on table procurement.purchase_returns
drop cascades to constraint purchase_requisitions_branch_id_fkey on table procurement.purchase_requisitions
drop cascades to constraint payments_branch_id_fkey on table financial.payments
drop cascades to constraint journal_entries_branch_id_fkey on table financial.journal_entries
drop cascades to constraint environmental_compliance_branch_id_fkey on table compliance.environmental_compliance
drop cascades to constraint org_licenses_branch_id_fkey on table compliance.org_licenses
drop cascades to constraint regulatory_inspections_branch_id_fkey on table compliance.regulatory_inspections
drop cascades to constraint system_settings_branch_id_fkey on table system_config.system_settings
drop cascades to table master.org_users
drop cascades to constraint products_created_by_fkey on table inventory.products
drop cascades to constraint stock_transfers_requested_by_fkey on table inventory.stock_transfers
drop cascades to constraint stock_transfers_approved_by_fkey on table inventory.stock_transfers
and 119 other objects (see server log for list)
DROP SCHEMA
psql:reset-database.sql:6: NOTICE:  drop cascades to 32 other objects
DETAIL:  drop cascades to table inventory.product_categories
drop cascades to constraint gst_rates_product_category_id_fkey on table gst.gst_rates
drop cascades to table inventory.product_types
drop cascades to table inventory.units_of_measure
drop cascades to table inventory.products
drop cascades to constraint order_items_product_id_fkey on table sales.order_items
drop cascades to constraint price_list_items_product_id_fkey on table sales.price_list_items
drop cascades to constraint purchase_order_items_product_id_fkey on table procurement.purchase_order_items
drop cascades to constraint grn_items_product_id_fkey on table procurement.grn_items
drop cascades to constraint purchase_requisition_items_product_id_fkey on table procurement.purchase_requisition_items
drop cascades to constraint supplier_quotation_items_product_id_fkey on table procurement.supplier_quotation_items
drop cascades to constraint gst_rates_product_id_fkey on table gst.gst_rates
drop cascades to constraint invoice_items_product_id_fkey on table sales.invoice_items
drop cascades to constraint delivery_challan_items_product_id_fkey on table sales.delivery_challan_items
drop cascades to constraint sales_return_items_product_id_fkey on table sales.sales_return_items
drop cascades to constraint purchase_return_items_product_id_fkey on table procurement.purchase_return_items
drop cascades to constraint quality_control_tests_product_id_fkey on table compliance.quality_control_tests
drop cascades to table inventory.storage_locations
drop cascades to constraint purchase_orders_delivery_location_id_fkey on table procurement.purchase_orders
drop cascades to constraint goods_receipt_notes_storage_location_id_fkey on table procurement.goods_receipt_notes
drop cascades to constraint grn_items_storage_location_id_fkey on table procurement.grn_items
drop cascades to table inventory.stock_transfers
drop cascades to table inventory.product_pack_configurations
drop cascades to table inventory.batches
drop cascades to constraint fk_return_items_batch on table sales.sales_return_items
drop cascades to constraint fk_purchase_return_items_batch on table procurement.purchase_return_items
drop cascades to constraint fk_qc_tests_batch on table compliance.quality_control_tests
drop cascades to table inventory.location_wise_stock
drop cascades to table inventory.stock_reservations
drop cascades to table inventory.inventory_movements
drop cascades to table inventory.stock_transfer_items
drop cascades to table inventory.reorder_suggestions
DROP SCHEMA
psql:reset-database.sql:7: NOTICE:  drop cascades to 25 other objects
DETAIL:  drop cascades to table parties.customers
drop cascades to constraint orders_customer_id_fkey on table sales.orders
drop cascades to constraint invoices_customer_id_fkey on table sales.invoices
drop cascades to constraint delivery_challans_customer_id_fkey on table sales.delivery_challans
drop cascades to constraint sales_returns_customer_id_fkey on table sales.sales_returns
drop cascades to constraint customer_visits_customer_id_fkey on table sales.customer_visits
drop cascades to constraint customer_outstanding_customer_id_fkey on table financial.customer_outstanding
drop cascades to table parties.suppliers
drop cascades to constraint purchase_orders_supplier_id_fkey on table procurement.purchase_orders
drop cascades to constraint goods_receipt_notes_supplier_id_fkey on table procurement.goods_receipt_notes
drop cascades to constraint supplier_invoices_supplier_id_fkey on table procurement.supplier_invoices
drop cascades to constraint purchase_returns_supplier_id_fkey on table procurement.purchase_returns
drop cascades to constraint purchase_requisition_items_suggested_supplier_id_fkey on table procurement.purchase_requisition_items
drop cascades to constraint supplier_quotations_supplier_id_fkey on table procurement.supplier_quotations
drop cascades to constraint vendor_performance_supplier_id_fkey on table procurement.vendor_performance
drop cascades to constraint supplier_outstanding_supplier_id_fkey on table financial.supplier_outstanding
drop cascades to table parties.customer_contacts
drop cascades to table parties.supplier_contacts
drop cascades to table parties.customer_groups
drop cascades to table parties.customer_group_members
drop cascades to table parties.territories
drop cascades to constraint orders_territory_id_fkey on table sales.orders
drop cascades to table parties.routes
drop cascades to constraint orders_route_id_fkey on table sales.orders
drop cascades to constraint customer_visits_route_id_fkey on table sales.customer_visits
DROP SCHEMA
psql:reset-database.sql:8: NOTICE:  drop cascades to 13 other objects
DETAIL:  drop cascades to table sales.orders
drop cascades to table sales.order_items
drop cascades to table sales.invoices
drop cascades to table sales.delivery_challans
drop cascades to table sales.sales_returns
drop cascades to table sales.price_lists
drop cascades to table sales.price_list_items
drop cascades to table sales.sales_schemes
drop cascades to table sales.sales_targets
drop cascades to table sales.customer_visits
drop cascades to table sales.invoice_items
drop cascades to table sales.delivery_challan_items
drop cascades to table sales.sales_return_items
DROP SCHEMA
psql:reset-database.sql:9: NOTICE:  drop cascades to 12 other objects
DETAIL:  drop cascades to table procurement.purchase_orders
drop cascades to table procurement.purchase_order_items
drop cascades to table procurement.goods_receipt_notes
drop cascades to table procurement.grn_items
drop cascades to table procurement.supplier_invoices
drop cascades to table procurement.purchase_returns
drop cascades to table procurement.purchase_requisitions
drop cascades to table procurement.purchase_requisition_items
drop cascades to table procurement.supplier_quotations
drop cascades to table procurement.supplier_quotation_items
drop cascades to table procurement.vendor_performance
drop cascades to table procurement.purchase_return_items
DROP SCHEMA
psql:reset-database.sql:10: NOTICE:  drop cascades to 15 other objects
DETAIL:  drop cascades to table financial.payment_methods
drop cascades to table financial.payments
drop cascades to table financial.payment_allocations
drop cascades to table financial.journal_entries
drop cascades to table financial.journal_entry_lines
drop cascades to table financial.chart_of_accounts
drop cascades to table financial.bank_reconciliations
drop cascades to table financial.bank_reconciliation_items
drop cascades to table financial.expense_categories
drop cascades to table financial.expense_claims
drop cascades to table financial.expense_claim_items
drop cascades to table financial.pdc_management
drop cascades to table financial.cash_flow_forecast
drop cascades to table financial.customer_outstanding
drop cascades to table financial.supplier_outstanding
DROP SCHEMA
psql:reset-database.sql:11: NOTICE:  drop cascades to 12 other objects
DETAIL:  drop cascades to table gst.hsn_sac_codes
drop cascades to table gst.gst_rates
drop cascades to table gst.gstr1_data
drop cascades to table gst.gstr2a_data
drop cascades to table gst.gstr2b_data
drop cascades to table gst.gstr3b_data
drop cascades to table gst.gst_reconciliation
drop cascades to table gst.eway_bills
drop cascades to table gst.gst_liability
drop cascades to table gst.gst_credit_ledger
drop cascades to table gst.gst_audit_trail
drop cascades to table gst.compliance_calendar
DROP SCHEMA
psql:reset-database.sql:12: NOTICE:  drop cascades to 12 other objects
DETAIL:  drop cascades to table compliance.license_types
drop cascades to table compliance.regulatory_authorities
drop cascades to table compliance.quality_deviations
drop cascades to table compliance.environmental_compliance
drop cascades to table compliance.environmental_breaches
drop cascades to table compliance.compliance_violations
drop cascades to table compliance.org_compliance_status
drop cascades to table compliance.org_licenses
drop cascades to table compliance.license_renewal_history
drop cascades to table compliance.regulatory_inspections
drop cascades to table compliance.corrective_action_plans
drop cascades to table compliance.quality_control_tests
DROP SCHEMA
psql:reset-database.sql:13: NOTICE:  drop cascades to 11 other objects
DETAIL:  drop cascades to table analytics.report_templates
drop cascades to table analytics.report_schedules
drop cascades to table analytics.report_execution_history
drop cascades to table analytics.dashboards
drop cascades to table analytics.dashboard_widgets
drop cascades to table analytics.kpi_definitions
drop cascades to table analytics.kpi_values
drop cascades to table analytics.data_quality_metrics
drop cascades to table analytics.user_activity_analytics
drop cascades to table analytics.alert_definitions
drop cascades to table analytics.alert_history
DROP SCHEMA
psql:reset-database.sql:14: NOTICE:  drop cascades to 13 other objects
DETAIL:  drop cascades to table system_config.audit_logs
drop cascades to table system_config.system_notifications
drop cascades to table system_config.user_notifications
drop cascades to table system_config.scheduled_jobs
drop cascades to table system_config.job_execution_history
drop cascades to table system_config.system_integrations
drop cascades to table system_config.integration_logs
drop cascades to table system_config.email_templates
drop cascades to table system_config.scheduled_notifications
drop cascades to table system_config.system_health_metrics
drop cascades to table system_config.error_logs
drop cascades to table system_config.system_settings
drop cascades to table system_config.feature_flags
DROP SCHEMA
DROP SCHEMA
DROP SCHEMA
            status            
------------------------------
 Schemas dropped successfully
(1 row)

✅ Database reset complete

Starting deployment...
1️⃣ Creating schemas...
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
CREATE SCHEMA
COMMENT
GRANT
GRANT
GRANT
GRANT
GRANT
GRANT
GRANT
GRANT
GRANT
GRANT
  schema_name  |                           description                            
---------------+------------------------------------------------------------------
 master        | Core master data: organizations, users, locations, configuration
 inventory     | Product, batch, stock, and warehouse management
 parties       | Customers, suppliers, and other business partners
 sales         | Orders, invoices, deliveries, and sales returns
 procurement   | Purchase orders, goods receipts, and supplier management
 financial     | Accounting, payments, banking, and financial reporting
 gst           | GST compliance, returns, and tax management
 compliance    | Licenses, inspections, and regulatory compliance
 analytics     | Business intelligence, KPIs, and reporting
 system_config | System settings, integrations, and monitoring
(10 rows)

✅ Schemas created

2️⃣ Creating tables...
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
psql:database/enterprise-v2/02-tables/02_inventory_tables.sql:582: ERROR:  relation "parties.suppliers" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
psql:database/enterprise-v2/02-tables/08_compliance_tables.sql:454: ERROR:  syntax error at or near ")"
LINE 52: );
         ^
psql:database/enterprise-v2/02-tables/08_compliance_tables.sql:487: ERROR:  relation "compliance.narcotic_register" does not exist
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/02-tables/08_compliance_tables.sql:691: ERROR:  relation "compliance.narcotic_register" does not exist
psql:database/enterprise-v2/02-tables/08_compliance_tables.sql:692: ERROR:  relation "compliance.narcotic_register" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
psql:database/enterprise-v2/02-tables/08_compliance_tables.sql:701: ERROR:  relation "compliance.narcotic_register" does not exist
COMMENT
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
✅ Tables created

3️⃣ Fixing missing columns and tables...
DO
DO
CREATE TABLE
              status              | narcotic_register_exists 
----------------------------------+--------------------------
 Fixed missing columns and tables |                        1
(1 row)

✅ Fixes applied

4️⃣ Adding foreign key constraints...
ALTER TABLE
psql:database/enterprise-v2/02-tables/99_add_foreign_keys.sql:12: ERROR:  column "batch_id" referenced in foreign key constraint does not exist
ALTER TABLE
ALTER TABLE
ALTER TABLE
ALTER TABLE
✅ Foreign keys added

5️⃣ Creating triggers...
Loading: 00_trigger_summary.sql
Loading: 01_financial_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 02_inventory_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/04-triggers/02_inventory_triggers.sql:726: ERROR:  relation "inventory.reorder_suggestions" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 03_sales_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 04_procurement_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/04-triggers/04_procurement_triggers.sql:660: ERROR:  syntax error at or near "USING"
LINE 1: ...ces_grn ON procurement.supplier_invoices(grn_ids) USING GIN;
                                                             ^
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 05_credit_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 06_gst_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:448: ERROR:  relation "gst.gstr_2a_data" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:614: ERROR:  relation "sales.dispatch_details" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:710: ERROR:  relation "gst.hsn_codes" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:789: ERROR:  relation "gst.gstr_3b_header" does not exist
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:946: ERROR:  relation "gst.gstr_1_header" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:951: ERROR:  relation "gst.gstr_3b_header" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:956: ERROR:  relation "gst.hsn_codes" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:957: ERROR:  relation "gst.gstr_1_b2b" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:958: ERROR:  relation "gst.gstr_2a_data" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:959: ERROR:  column "reference_type" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:960: ERROR:  relation "gst.tds_entries" does not exist
psql:database/enterprise-v2/04-triggers/06_gst_triggers.sql:961: ERROR:  relation "gst.audit_trail" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 07_compliance_triggers.sql
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:171: ERROR:  syntax error at or near "->>"
LINE 96: ... (org_id, notification_category, notification_data->>'licens...
                                                              ^
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:176: ERROR:  relation "compliance.licenses" does not exist
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1027: ERROR:  relation "compliance.temperature_logs" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1179: ERROR:  relation "compliance.product_recalls" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1184: ERROR:  relation "compliance.licenses" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1185: ERROR:  column "location_id" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1186: ERROR:  relation "compliance.inspection_findings" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1187: ERROR:  column "status" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1188: ERROR:  relation "compliance.temperature_logs" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1189: ERROR:  relation "compliance.gxp_audit_trail" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1190: ERROR:  relation "compliance.product_recalls" does not exist
psql:database/enterprise-v2/04-triggers/07_compliance_triggers.sql:1193: ERROR:  function monitor_license_expiry() does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 07_gst_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
Loading: 08_analytics_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:391: ERROR:  relation "system_config.system_health_checks" does not exist
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:894: ERROR:  relation "analytics.kpi_actuals" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:895: ERROR:  relation "analytics.kpi_alerts" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:896: ERROR:  column "next_run_at" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:897: ERROR:  relation "analytics.data_quality_issues" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:898: ERROR:  relation "analytics.customer_predictions" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:899: ERROR:  relation "analytics.performance_metrics" does not exist
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:900: ERROR:  relation "analytics.dashboard_cache" does not exist
COMMENT
psql:database/enterprise-v2/04-triggers/08_analytics_triggers.sql:904: ERROR:  function check_kpi_thresholds() does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 08_compliance_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
Loading: 09_system_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:493: ERROR:  relation "system_config.workflow_instances" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:633: ERROR:  relation "system_config.system_health_checks" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:779: ERROR:  relation "system_config.api_usage_log" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:944: ERROR:  relation "system_config.backup_history" does not exist
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1070: ERROR:  relation "system_config.user_sessions" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1075: ERROR:  relation "system_config.configuration_history" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1076: ERROR:  column "acknowledged" does not exist
LINE 1: ....system_notifications(org_id, acknowledged) WHERE acknowledg...
                                                             ^
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1077: ERROR:  relation "system_config.workflow_instances" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1078: ERROR:  relation "system_config.system_alerts" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1079: ERROR:  relation "system_config.api_usage_log" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1080: ERROR:  relation "system_config.backup_history" does not exist
psql:database/enterprise-v2/04-triggers/09_system_triggers.sql:1081: ERROR:  relation "system_config.user_sessions" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 10_pricing_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/10_pricing_triggers.sql:778: ERROR:  relation "inventory.competitor_pricing" does not exist
CREATE TABLE
psql:database/enterprise-v2/04-triggers/10_pricing_triggers.sql:825: ERROR:  type "idx_price_history_product" does not exist
LINE 14:     INDEX idx_price_history_product (product_id, changed_at)...
                   ^
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 11_core_operations_triggers.sql
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE TRIGGER
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
CREATE TRIGGER
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/11_core_operations_triggers.sql:815: ERROR:  column new.auto_allocate does not exist
LINE 4:     WHEN (NEW.payment_status = 'cleared' AND NEW.auto_alloca...
                                                     ^
CREATE FUNCTION
psql:database/enterprise-v2/04-triggers/11_core_operations_triggers.sql:930: ERROR:  relation "system_config.system_health_checks" does not exist
psql:database/enterprise-v2/04-triggers/11_core_operations_triggers.sql:935: ERROR:  column "batch_allocation" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
✅ Triggers created

6️⃣ Creating business functions...
Loading: 01_financial_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 02_inventory_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 03_sales_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:912: ERROR:  syntax error at or near "LIMIT"
LINE 48:         LIMIT 10
                 ^
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1045: ERROR:  syntax error at or near "LIMIT"
LINE 63:         LIMIT 5
                 ^
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1053: ERROR:  column "valid_from" does not exist
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1054: ERROR:  column "return_status" does not exist
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1059: ERROR:  role "sales_user" does not exist
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1060: ERROR:  function name "generate_invoice_from_order" is not unique
HINT:  Specify the argument list to select the function unambiguously.
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1061: ERROR:  function name "process_sales_return" is not unique
HINT:  Specify the argument list to select the function unambiguously.
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1062: ERROR:  could not find a function named "get_customer_sales_analytics"
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1063: ERROR:  could not find a function named "track_sales_targets"
COMMENT
COMMENT
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1070: ERROR:  function name "generate_invoice_from_order" is not unique
HINT:  Specify the argument list to select the function unambiguously.
COMMENT
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1072: ERROR:  function name "process_sales_return" is not unique
HINT:  Specify the argument list to select the function unambiguously.
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1073: ERROR:  could not find a function named "get_customer_sales_analytics"
psql:database/enterprise-v2/05-functions/03_sales_functions.sql:1074: ERROR:  could not find a function named "track_sales_targets"
Loading: 04_procurement_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE TABLE
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:994: ERROR:  type "idx_consumption_product_date" does not exist
LINE 12:     INDEX idx_consumption_product_date (product_id, calculat...
                   ^
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:1007: ERROR:  role "procurement_user" does not exist
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:1008: ERROR:  role "warehouse_user" does not exist
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:1009: ERROR:  role "procurement_manager" does not exist
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:1010: ERROR:  role "system" does not exist
psql:database/enterprise-v2/05-functions/04_procurement_functions.sql:1011: ERROR:  role "finance_user" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 05_gst_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/05-functions/05_gst_functions.sql:1096: ERROR:  role "gst_user" does not exist
psql:database/enterprise-v2/05-functions/05_gst_functions.sql:1097: ERROR:  role "gst_user" does not exist
psql:database/enterprise-v2/05-functions/05_gst_functions.sql:1098: ERROR:  role "sales_user" does not exist
psql:database/enterprise-v2/05-functions/05_gst_functions.sql:1099: ERROR:  role "gst_user" does not exist
psql:database/enterprise-v2/05-functions/05_gst_functions.sql:1100: ERROR:  role "gst_user" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 06_compliance_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE TABLE
CREATE TABLE
CREATE TABLE
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1058: ERROR:  relation "compliance.business_licenses" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1059: ERROR:  relation "compliance.narcotic_drug_register" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1060: ERROR:  relation "compliance.inspection_findings" does not exist
CREATE INDEX
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1062: ERROR:  relation "compliance.gxp_audit_log" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1067: ERROR:  role "compliance_officer" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1068: ERROR:  role "pharmacist" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1069: ERROR:  role "quality_manager" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1070: ERROR:  role "quality_user" does not exist
psql:database/enterprise-v2/05-functions/06_compliance_functions.sql:1071: ERROR:  role "auditor" does not exist
COMMENT
COMMENT
COMMENT
COMMENT
COMMENT
Loading: 07_analytics_functions.sql
CREATE FUNCTION
CREATE FUNCTION
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:957: ERROR:  syntax error at or near "LIMIT"
LINE 72:                 LIMIT 10
                         ^
CREATE FUNCTION
CREATE FUNCTION
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1494: ERROR:  column "batch_allocation" does not exist
CREATE INDEX
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1501: ERROR:  role "executive" does not exist
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1502: ERROR:  role "sales_manager" does not exist
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1503: ERROR:  could not find a function named "analyze_inventory_optimization"
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1504: ERROR:  role "sales_manager" does not exist
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1505: ERROR:  role "finance_manager" does not exist
COMMENT
COMMENT
psql:database/enterprise-v2/05-functions/07_analytics_functions.sql:1512: ERROR:  could not find a function named "analyze_inventory_optimization"
COMMENT
COMMENT
Loading: 08_system_functions.sql
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE FUNCTION
CREATE TABLE
CREATE TABLE
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1038: ERROR:  type "idx_api_logs_time" does not exist
LINE 13:     INDEX idx_api_logs_time (created_at, status)
                   ^
CREATE TABLE
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1059: ERROR:  relation "system_config.users" does not exist
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1060: ERROR:  relation "system_config.user_sessions" does not exist
CREATE INDEX
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1062: ERROR:  relation "system_config.audit_log" does not exist
CREATE INDEX
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1068: ERROR:  role "admin" does not exist
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1069: ERROR:  role "admin" does not exist
GRANT
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1071: ERROR:  function name "monitor_system_health" is not unique
HINT:  Specify the argument list to select the function unambiguously.
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1072: ERROR:  role "admin" does not exist
COMMENT
COMMENT
COMMENT
psql:database/enterprise-v2/05-functions/08_system_functions.sql:1080: ERROR:  function name "monitor_system_health" is not unique
HINT:  Specify the argument list to select the function unambiguously.
COMMENT
✅ Functions created

7️⃣ Creating performance indexes...
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:14: ERROR:  column "gstin" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:17: ERROR:  relation "master.branches" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:18: ERROR:  relation "master.branches" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:19: ERROR:  relation "master.branches" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:22: ERROR:  relation "master.product_categories" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:23: ERROR:  relation "master.product_categories" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:24: ERROR:  relation "master.product_categories" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:27: ERROR:  relation "master.pack_configurations" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:30: ERROR:  relation "master.units_of_measurement" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:49: ERROR:  column "narcotic_balance" does not exist
LINE 1: ...ntory.batches(product_id, narcotic_balance) WHERE narcotic_b...
                                                             ^
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:54: ERROR:  column "is_sales_location" does not exist
LINE 1: ...age_locations(branch_id, is_sales_location) WHERE is_sales_l...
                                                             ^
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:76: ERROR:  relation "inventory.stock_adjustments" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:77: ERROR:  relation "inventory.stock_adjustments" does not exist
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:86: ERROR:  column "gstin" does not exist
LINE 1: ...customers_gstin ON parties.customers(gstin) WHERE gstin IS N...
                                                             ^
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:87: ERROR:  column "primary_phone" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:88: ERROR:  column "category_id" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:94: ERROR:  column "gstin" does not exist
LINE 1: ...suppliers_gstin ON parties.suppliers(gstin) WHERE gstin IS N...
                                                             ^
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:98: ERROR:  relation "parties.customer_categories" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:101: ERROR:  relation "parties.customer_outstanding" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:102: ERROR:  relation "parties.customer_outstanding" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:103: ERROR:  relation "parties.customer_outstanding" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:120: ERROR:  column "delivery_status" does not exist
LINE 1: ...ivery ON sales.order_items(delivery_status) WHERE delivery_s...
                                                             ^
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:134: ERROR:  column "batch_allocation" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:143: ERROR:  column "valid_from" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:144: ERROR:  column "branch_id" does not exist
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:149: ERROR:  column "customer_category_id" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:152: ERROR:  column "valid_from" does not exist
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:154: ERROR:  column "branches" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:168: ERROR:  column "po_id" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:170: ERROR:  column "quantity_ordered" does not exist
LINE 1: ...chase_order_items(po_id, quantity_received) WHERE quantity_o...
                                                             ^
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:174: ERROR:  column "po_id" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:186: ERROR:  column "grn_id" does not exist
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:195: ERROR:  relation "procurement.supplier_products" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:196: ERROR:  relation "procurement.supplier_products" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:203: ERROR:  column "entry_date" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:204: ERROR:  column "posting_status" does not exist
LINE 1: ...N financial.journal_entries(posting_status) WHERE posting_st...
                                                             ^
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:205: ERROR:  column "entry_number" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:209: ERROR:  column "entry_id" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:210: ERROR:  column "account_id" does not exist
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:216: ERROR:  column "reference_type" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:217: ERROR:  column "payment_mode" does not exist
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:225: ERROR:  column "maturity_date" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:244: ERROR:  column "invoice_id" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:248: ERROR:  column "supplier_gstin" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:251: ERROR:  relation "gst.gstr3b_summary" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:254: ERROR:  relation "gst.gst_returns" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:255: ERROR:  relation "gst.gst_returns" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:258: ERROR:  column "invoice_id" does not exist
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:267: ERROR:  relation "compliance.business_licenses" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:268: ERROR:  relation "compliance.business_licenses" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:269: ERROR:  relation "compliance.business_licenses" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:272: ERROR:  relation "compliance.narcotic_drug_register" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:273: ERROR:  relation "compliance.narcotic_drug_register" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:274: ERROR:  relation "compliance.narcotic_drug_register" does not exist
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:281: ERROR:  relation "compliance.inspection_findings" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:282: ERROR:  relation "compliance.inspection_findings" does not exist
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:286: ERROR:  column "product_id" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:290: ERROR:  relation "compliance.gxp_audit_log" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:291: ERROR:  relation "compliance.gxp_audit_log" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:298: ERROR:  relation "analytics.kpi_metrics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:299: ERROR:  relation "analytics.kpi_metrics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:302: ERROR:  relation "analytics.sales_analytics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:303: ERROR:  relation "analytics.sales_analytics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:304: ERROR:  relation "analytics.sales_analytics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:307: ERROR:  relation "analytics.inventory_analytics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:308: ERROR:  relation "analytics.inventory_analytics" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:311: ERROR:  relation "analytics.customer_behavior" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:312: ERROR:  relation "analytics.customer_behavior" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:315: ERROR:  relation "analytics.product_performance" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:316: ERROR:  relation "analytics.product_performance" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:323: ERROR:  relation "system_config.users" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:324: ERROR:  relation "system_config.users" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:327: ERROR:  relation "system_config.user_sessions" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:328: ERROR:  relation "system_config.user_sessions" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:331: ERROR:  relation "system_config.user_roles" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:332: ERROR:  relation "system_config.user_roles" does not exist
CREATE INDEX
CREATE INDEX
CREATE INDEX
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:340: ERROR:  column "delivery_status" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:343: ERROR:  relation "system_config.audit_log" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:344: ERROR:  relation "system_config.audit_log" does not exist
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:362: ERROR:  column "product_description" does not exist
LINE 7:         COALESCE(product_description, '')
                         ^
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:372: ERROR:  column "contact_person" does not exist
LINE 5:         COALESCE(contact_person, '') || ' ' ||
                         ^
psql:database/enterprise-v2/06-indexes/01_performance_indexes.sql:382: ERROR:  column "contact_person" does not exist
LINE 5:         COALESCE(contact_person, '') || ' ' ||
                         ^
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE INDEX
CREATE EXTENSION
CREATE FUNCTION
COMMENT
✅ Indexes created

8️⃣ Creating API functions...
Loading: 01_master_apis.sql
psql:database/enterprise-v2/08-api/01_master_apis.sql:57: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:141: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:212: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:268: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:343: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:384: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:430: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:464: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:467: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:468: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:469: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:470: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:471: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:472: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:473: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:474: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:476: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:477: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:478: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:479: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:480: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:481: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:482: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/01_master_apis.sql:483: ERROR:  schema "api" does not exist
Loading: 02_inventory_apis.sql
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:77: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:148: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:213: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:314: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:388: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:481: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:484: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:485: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:486: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:487: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:488: ERROR:  schema "api" does not exist
^[psql:database/enterprise-v2/08-api/02_inventory_apis.sql:489: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:491: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:492: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:493: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:494: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:495: ERROR:  schema "api" does not exist
psql:database/enterprise-v2/08-api/02_inventory_apis.sql:496: ERROR:  schema "api" does not exist
Loading: 03_sales_apis.sql
