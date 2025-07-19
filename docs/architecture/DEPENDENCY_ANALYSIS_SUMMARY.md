# Dependency Analysis Summary

## Overview
- **Total Files Analyzed**: 61
- **Total Functions**: 573
- **Total Classes**: 165
- **Circular Dependencies Found**: 0
- **Files with Unused Imports**: 56
- **Total Unused Code Elements**: 497

## Component Breakdown

### base_schemas.py
- Files: 1
- Functions: 0
- Classes: 25
- External Dependencies: 11

### models.py
- Files: 1
- Functions: 0
- Classes: 11
- External Dependencies: 13

### database.py
- Files: 1
- Functions: 3
- Classes: 0
- External Dependencies: 9

### schemas.py
- Files: 1
- Functions: 0
- Classes: 47
- External Dependencies: 18

### business_logic.py
- Files: 1
- Functions: 22
- Classes: 6
- External Dependencies: 20

### initialize_db.py
- Files: 1
- Functions: 1
- Classes: 0
- External Dependencies: 6

### main.py
- Files: 1
- Functions: 0
- Classes: 0
- External Dependencies: 39

### crud.py
- Files: 1
- Functions: 196
- Classes: 0
- External Dependencies: 20

### dependencies.py
- Files: 1
- Functions: 1
- Classes: 0
- External Dependencies: 16

### routers
- Files: 28
- Functions: 243
- Classes: 3
- External Dependencies: 57

### migrations
- Files: 8
- Functions: 17
- Classes: 0
- External Dependencies: 25

### core
- Files: 6
- Functions: 53
- Classes: 14
- External Dependencies: 59

### schemas_v2
- Files: 5
- Functions: 7
- Classes: 55
- External Dependencies: 19

### services
- Files: 5
- Functions: 30
- Classes: 4
- External Dependencies: 22

## Unused Functions

- get_expiring_licenses
- can_execute
- create_product
- delete_sales_return
- read_customer
- create_price_history
- create_challan_from_order
- create_loyalty_program
- get_customer_documents
- get_drug_licensing_report
- ... and 412 more

## Database Table Usage

- **CURRENT_DATE**: Used in 1 files
- **ON**: Used in 2 files
- **batches**: Used in 6 files
- **customers**: Used in 7 files
- **information_schema**: Used in 7 files
- **inventory_movements**: Used in 5 files
- **invoice_date**: Used in 1 files
- **invoice_items**: Used in 3 files
- **invoice_payments**: Used in 2 files
- **invoices**: Used in 6 files
- **order_items**: Used in 5 files
- **orders**: Used in 8 files
- **organizations**: Used in 4 files
- **payments**: Used in 1 files
- **products**: Used in 7 files
- **sales_returns**: Used in 1 files

## API Endpoints

- `DELETE /items/{order_item_id}` → api/routers/orders.py
- `DELETE /items/{purchase_item_id}` → api/routers/purchases.py
- `DELETE /movements/{movement_id}` → api/routers/inventory.py
- `DELETE /suppliers/{supplier_id}` → api/routers/purchases.py
- `DELETE /vendor/{vendor_payment_id}` → api/routers/payments.py
- `DELETE /{batch_id}` → api/routers/batches.py
- `DELETE /{challan_id}` → api/routers/challans.py
- `DELETE /{challan_id}/items/{item_id}` → api/routers/challans.py
- `DELETE /{customer_id}` → api/routers/customers.py
- `DELETE /{file_id}` → api/routers/file_uploads.py
- `DELETE /{order_id}` → api/routers/orders.py
- `DELETE /{payment_id}` → api/routers/payments.py
- `DELETE /{product_id}` → api/routers/products.py
- `DELETE /{purchase_id}` → api/routers/purchases.py
- `DELETE /{return_id}` → api/routers/sales_returns.py
- `DELETE /{tax_entry_id}` → api/routers/tax_entries.py
- `DELETE /{user_id}` → api/routers/users.py
- `GET /` → api/routers/v1/customers.py
- `GET /accounts/` → api/routers/loyalty.py
- `GET /accounts/customer/{customer_id}` → api/routers/loyalty.py
- `GET /accounts/{account_id}` → api/routers/loyalty.py
- `GET /alerts` → api/routers/inventory.py
- `GET /allocations/` → api/routers/payments.py
- `GET /analytics/audit-trail` → api/routers/compliance.py
- `GET /analytics/by-reason` → api/routers/stock_adjustments.py
- `GET /analytics/customer-engagement` → api/routers/loyalty.py
- `GET /analytics/delivery-performance` → api/routers/challans.py
- `GET /analytics/expiry-timeline` → api/routers/batches.py
- `GET /analytics/recent` → api/routers/file_uploads.py
- `GET /analytics/summary` → api/routers/loyalty.py
- `GET /analytics/tier-performance` → api/routers/loyalty.py
- `GET /audit-logs/` → api/routers/compliance.py
- `GET /audit-logs/{log_id}` → api/routers/compliance.py
- `GET /batch-locations/` → api/routers/inventory.py
- `GET /batch-locations/{batch_location_id}` → api/routers/inventory.py
- `GET /batch-status/{batch_id}` → api/routers/inventory.py
- `GET /batch/{batch_id}/adjustments` → api/routers/stock_adjustments.py
- `GET /batches` → api/routers/v1/inventory.py
- `GET /batches/{batch_id}` → api/routers/v1/inventory.py
- `GET /check-billing-tables` → api/routers/migrations_v2.py
- `GET /check-customer-columns` → api/routers/migrations_v2.py
- `GET /check-inventory-tables` → api/routers/migrations_v2.py
- `GET /checks/` → api/routers/compliance.py
- `GET /checks/{check_id}` → api/routers/compliance.py
- `GET /compliance/certificates` → api/routers/file_uploads.py
- `GET /compliance/licenses` → api/routers/file_uploads.py
- `GET /compliance/pending-returns` → api/routers/tax_entries.py
- `GET /credit-notes/` → api/routers/customers.py
- `GET /credit-notes/{credit_note_id}` → api/routers/customers.py
- `GET /customer/{customer_id}` → api/routers/challans.py
- `GET /customer/{customer_id}/bills` → api/routers/orders.py
- `GET /customer/{customer_id}/documents` → api/routers/file_uploads.py
- `GET /customer/{customer_id}/pending` → api/routers/challans.py
- `GET /customer/{customer_id}/returns` → api/routers/sales_returns.py
- `GET /customers/segmentation` → api/routers/analytics.py
- `GET /dashboard` → api/routers/v1/inventory.py
- `GET /dashboard/overview` → api/routers/analytics.py
- `GET /dashboard/sales-trend` → api/routers/analytics.py
- `GET /dashboard/stats` → api/routers/v1/orders.py
- `GET /download/{unique_filename}` → api/routers/file_uploads.py
- `GET /entity/{entity_type}/{entity_id}` → api/routers/file_uploads.py
- `GET /expiry/alerts` → api/routers/v1/inventory.py
- `GET /expiry/by-month/{year}/{month}` → api/routers/batches.py
- `GET /expiry/expired` → api/routers/batches.py
- `GET /expiry/expiring-soon` → api/routers/batches.py
- `GET /export/comprehensive-report` → api/routers/analytics.py
- `GET /fifo-allocation/{product_id}` → api/routers/inventory.py
- `GET /financial/cash-flow` → api/routers/analytics.py
- `GET /financial/summary` → api/routers/analytics.py
- `GET /full-schema` → api/routers/db_inspect.py
- `GET /gst/gstr1` → api/routers/v1/billing.py
- `GET /inventory/status` → api/routers/analytics.py
- `GET /inventory/turnover` → api/routers/analytics.py
- `GET /invoices` → api/routers/v1/billing.py
- `GET /invoices/{invoice_id}` → api/routers/v1/billing.py
- `GET /invoices/{invoice_id}/print` → api/routers/v1/billing.py
- `GET /items/` → api/routers/orders.py
- `GET /items/{order_item_id}` → api/routers/orders.py
- `GET /items/{purchase_item_id}` → api/routers/purchases.py
- `GET /licenses/` → api/routers/compliance.py
- `GET /licenses/alerts/expiring` → api/routers/compliance.py
- `GET /licenses/{license_id}` → api/routers/compliance.py
- `GET /list` → api/routers/organizations.py
- `GET /low-stock/` → api/routers/inventory.py
- `GET /me` → api/routers/users.py
- `GET /migration-plan` → api/routers/migrations_v2.py
- `GET /movements` → api/routers/v1/inventory.py
- `GET /movements/` → api/routers/inventory.py
- `GET /movements/{movement_id}` → api/routers/inventory.py
- `GET /operations/efficiency` → api/routers/analytics.py
- `GET /order/{order_id}/returns` → api/routers/sales_returns.py
- `GET /order/{order_id}/status` → api/routers/simple_delivery.py
- `GET /order/{order_id}/tax-summary` → api/routers/tax_entries.py
- `GET /out-of-stock/` → api/routers/inventory.py
- `GET /outstanding/` → api/routers/customers.py
- `GET /outstanding/{outstanding_id}` → api/routers/customers.py
- `GET /parser/health` → api/routers/purchases.py
- `GET /payments` → api/routers/v1/billing.py
- `GET /pending` → api/routers/simple_delivery.py
- `GET /points/transactions/{account_id}` → api/routers/loyalty.py
- `GET /predictions/demand-forecast` → api/routers/analytics.py
- `GET /product/{product_id}/batches` → api/routers/batches.py
- `GET /product/{product_id}/images` → api/routers/file_uploads.py
- `GET /query` → api/routers/db_inspect.py
- `GET /reports/` → api/routers/compliance.py
- `GET /reports/daily` → api/routers/challans.py
- `GET /reports/drug-licensing` → api/routers/compliance.py
- `GET /reports/generate/monthly` → api/routers/compliance.py
- `GET /reports/gst-summary` → api/routers/tax_entries.py
- `GET /reports/summary` → api/routers/tax_entries.py
- `GET /reports/wastage-analysis` → api/routers/batches.py
- `GET /reports/{report_id}` → api/routers/compliance.py
- `GET /return-items/return/{return_id}` → api/routers/purchases.py
- `GET /return-items/{return_item_id}` → api/routers/purchases.py
- `GET /returns/` → api/routers/purchases.py
- `GET /returns/{return_id}` → api/routers/purchases.py
- `GET /rewards/` → api/routers/loyalty.py
- `GET /rewards/customer/{customer_id}` → api/routers/loyalty.py
- `GET /rewards/redemptions/{customer_id}` → api/routers/loyalty.py
- `GET /rewards/{reward_id}` → api/routers/loyalty.py
- `GET /roles/` → api/routers/users.py
- `GET /sales/summary` → api/routers/analytics.py
- `GET /sales/top-products` → api/routers/analytics.py
- `GET /search/batch-number/{batch_number}` → api/routers/batches.py
- `GET /sessions/active` → api/routers/users.py
- `GET /stats` → api/routers/simple_delivery.py
- `GET /stock/current` → api/routers/v1/inventory.py
- `GET /stock/current/{product_id}` → api/routers/v1/inventory.py
- `GET /storage-locations/` → api/routers/inventory.py
- `GET /storage-locations/{location_id}` → api/routers/inventory.py
- `GET /summary` → api/routers/v1/billing.py
- `GET /supplier/{supplier_id}/batches` → api/routers/batches.py
- `GET /suppliers/` → api/routers/purchases.py
- `GET /suppliers/{supplier_id}` → api/routers/purchases.py
- `GET /suppliers/{supplier_id}/analytics` → api/routers/purchases.py
- `GET /table/{table_name}/columns` → api/routers/db_inspect.py
- `GET /tables` → api/routers/db_inspect.py
- `GET /tiers/benefits/{tier}` → api/routers/loyalty.py
- `GET /transactions/` → api/routers/inventory.py
- `GET /transactions/batch/{batch_id}` → api/routers/inventory.py
- `GET /upi/customer/{customer_id}/payments` → api/routers/payments.py
- `GET /upi/qr-image/{merchant_tx_id}` → api/routers/payments.py
- `GET /upi/{merchant_tx_id}` → api/routers/payments.py
- `GET /valuation` → api/routers/v1/inventory.py
- `GET /vendor/` → api/routers/payments.py
- `GET /vendor/{vendor_payment_id}` → api/routers/payments.py
- `GET /{adjustment_id}` → api/routers/stock_adjustments.py
- `GET /{batch_id}` → api/routers/batches.py
- `GET /{batch_id}/current-stock` → api/routers/batches.py
- `GET /{challan_id}` → api/routers/challans.py
- `GET /{challan_id}/items/` → api/routers/challans.py
- `GET /{challan_id}/print-data` → api/routers/challans.py
- `GET /{customer_id}` → api/routers/v1/customers.py
- `GET /{customer_id}/active-challans` → api/routers/customers.py
- `GET /{customer_id}/advance-balance` → api/routers/customers.py
- `GET /{customer_id}/advance-payments` → api/routers/customers.py
- `GET /{customer_id}/ledger` → api/routers/v1/customers.py
- `GET /{customer_id}/orders` → api/routers/customers_simple.py
- `GET /{customer_id}/outstanding` → api/routers/v1/customers.py
- `GET /{customer_id}/payment-summary` → api/routers/customers.py
- `GET /{file_id}` → api/routers/file_uploads.py
- `GET /{order_id}` → api/routers/v1/orders.py
- `GET /{order_id}/bills` → api/routers/orders.py
- `GET /{order_id}/download-bill/{file_id}` → api/routers/orders.py
- `GET /{order_id}/payment-status` → api/routers/orders.py
- `GET /{payment_id}` → api/routers/payments.py
- `GET /{product_id}` → api/routers/products.py
- `GET /{purchase_id}` → api/routers/purchases.py
- `GET /{purchase_id}/download-invoice/{file_id}` → api/routers/purchases.py
- `GET /{purchase_id}/invoices` → api/routers/purchases.py
- `GET /{purchase_id}/parse-confidence` → api/routers/purchases.py
- `GET /{return_id}` → api/routers/sales_returns.py
- `GET /{tax_entry_id}` → api/routers/tax_entries.py
- `GET /{user_id}` → api/routers/users.py
- `POST /` → api/routers/v1/customers.py
- `POST /accounts/` → api/routers/loyalty.py
- `POST /add-customer-columns` → api/routers/migrations_v2.py
- `POST /add-inventory-tables` → api/routers/migrations_v2.py
- `POST /add-order-columns` → api/routers/migrations_v2.py
- `POST /advance/` → api/routers/payments.py
- `POST /apply-advance/` → api/routers/payments.py
- `POST /audit-logs/` → api/routers/compliance.py
- `POST /batch-locations/` → api/routers/inventory.py
- `POST /batch/{batch_id}/adjust` → api/routers/stock_adjustments.py
- `POST /batches` → api/routers/v1/inventory.py
- `POST /bulk/mark-delivered` → api/routers/simple_delivery.py
- `POST /calculate` → api/routers/tax_entries.py
- `POST /challan/{challan_id}/delivered` → api/routers/simple_delivery.py
- `POST /change-password` → api/routers/users.py
- `POST /checks/` → api/routers/compliance.py
- `POST /complete/` → api/routers/orders.py
- `POST /compliance/upload-certificate` → api/routers/file_uploads.py
- `POST /create-billing-tables` → api/routers/migrations_v2.py
- `POST /create-default` → api/routers/organizations.py
- `POST /create-from-invoice` → api/routers/purchases.py
- `POST /create-sample-customers` → api/routers/migrations_v2.py
- `POST /create-sample-orders` → api/routers/migrations_v2.py
- `POST /credit-notes/` → api/routers/customers.py
- `POST /fix-column/{table_name}` → api/routers/db_inspect.py
- `POST /fix-order-columns` → api/routers/migrations_v2.py
- `POST /from-order/{order_id}` → api/routers/challans.py
- `POST /invoices` → api/routers/v1/billing.py
- `POST /items/` → api/routers/orders.py
- `POST /licenses/` → api/routers/compliance.py
- `POST /login` → api/routers/users.py
- `POST /logout` → api/routers/users.py
- `POST /movements` → api/routers/v1/inventory.py
- `POST /movements/` → api/routers/inventory.py
- `POST /order/{order_id}/delivered` → api/routers/simple_delivery.py
- `POST /outstanding/` → api/routers/customers.py
- `POST /parse-invoice` → api/routers/purchases.py
- `POST /payments` → api/routers/v1/billing.py
- `POST /points/earn` → api/routers/loyalty.py
- `POST /points/redeem` → api/routers/loyalty.py
- `POST /register` → api/routers/users.py
- `POST /reports/` → api/routers/compliance.py
- `POST /reports/audit-export` → api/routers/compliance.py
- `POST /return-items/` → api/routers/purchases.py
- `POST /returns/` → api/routers/purchases.py
- `POST /rewards/` → api/routers/loyalty.py
- `POST /rewards/redeem` → api/routers/loyalty.py
- `POST /roles/` → api/routers/users.py
- `POST /run-org-id-migration` → api/routers/migrations.py
- `POST /stock/adjustment` → api/routers/v1/inventory.py
- `POST /storage-locations/` → api/routers/inventory.py
- `POST /suppliers/` → api/routers/purchases.py
- `POST /tiers/upgrade/{customer_id}` → api/routers/loyalty.py
- `POST /transactions/` → api/routers/inventory.py
- `POST /upi/generate-qr/` → api/routers/payments.py
- `POST /upload` → api/routers/file_uploads.py
- `POST /upload-multiple` → api/routers/file_uploads.py
- `POST /vendor/` → api/routers/payments.py
- `POST /with-allocation/` → api/routers/payments.py
- `POST /{batch_id}/mark-expired` → api/routers/batches.py
- `POST /{challan_id}/cancel` → api/routers/challans.py
- `POST /{challan_id}/deliver` → api/routers/challans.py
- `POST /{challan_id}/dispatch` → api/routers/challans.py
- `POST /{challan_id}/items/` → api/routers/challans.py
- `POST /{customer_id}/check-credit` → api/routers/v1/customers.py
- `POST /{customer_id}/payment` → api/routers/v1/customers.py
- `POST /{order_id}/generate-bill` → api/routers/orders.py
- `POST /{order_id}/invoice` → api/routers/v1/orders.py
- `POST /{order_id}/return` → api/routers/v1/orders.py
- `POST /{order_id}/upload-bill` → api/routers/orders.py
- `POST /{purchase_id}/upload-invoice` → api/routers/purchases.py
- `POST /{return_id}/process` → api/routers/sales_returns.py
- `PUT /accounts/{account_id}` → api/routers/loyalty.py
- `PUT /advance/{advance_payment_id}` → api/routers/payments.py
- `PUT /batch-locations/{batch_location_id}` → api/routers/inventory.py
- `PUT /checks/{check_id}/resolve` → api/routers/compliance.py
- `PUT /credit-notes/{credit_note_id}` → api/routers/customers.py
- `PUT /invoices/{invoice_id}/cancel` → api/routers/v1/billing.py
- `PUT /items/{order_item_id}` → api/routers/orders.py
- `PUT /items/{purchase_item_id}` → api/routers/purchases.py
- `PUT /licenses/{license_id}` → api/routers/compliance.py
- `PUT /me` → api/routers/users.py
- `PUT /movements/{movement_id}` → api/routers/inventory.py
- `PUT /order/{order_id}/status` → api/routers/simple_delivery.py
- `PUT /outstanding/{outstanding_id}` → api/routers/customers.py
- `PUT /reports/{report_id}/submit` → api/routers/compliance.py
- `PUT /returns/{return_id}` → api/routers/purchases.py
- `PUT /storage-locations/{location_id}` → api/routers/inventory.py
- `PUT /suppliers/{supplier_id}` → api/routers/purchases.py
- `PUT /upi/reconcile/{upi_payment_id}` → api/routers/payments.py
- `PUT /upi/update-status/{merchant_tx_id}` → api/routers/payments.py
- `PUT /vendor/{vendor_payment_id}` → api/routers/payments.py
- `PUT /{batch_id}` → api/routers/batches.py
- `PUT /{challan_id}` → api/routers/challans.py
- `PUT /{challan_id}/items/{item_id}` → api/routers/challans.py
- `PUT /{customer_id}` → api/routers/v1/customers.py
- `PUT /{order_id}` → api/routers/orders.py
- `PUT /{order_id}/confirm` → api/routers/v1/orders.py
- `PUT /{order_id}/deliver` → api/routers/v1/orders.py
- `PUT /{payment_id}` → api/routers/payments.py
- `PUT /{product_id}` → api/routers/products.py
- `PUT /{purchase_id}` → api/routers/purchases.py
- `PUT /{return_id}` → api/routers/sales_returns.py
- `PUT /{tax_entry_id}` → api/routers/tax_entries.py
- `PUT /{user_id}` → api/routers/users.py
