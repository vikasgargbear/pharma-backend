-- =====================================================
-- SCRIPT 01: Create Archive Tables
-- Purpose: Create archive tables for historical data
-- =====================================================

-- Create archive schema
CREATE SCHEMA IF NOT EXISTS archive;

-- Archive for orders older than 2 years
CREATE TABLE archive.orders AS 
SELECT * FROM orders 
WHERE created_at < CURRENT_DATE - INTERVAL '2 years'
LIMIT 0; -- Create structure only

-- Archive for order_items
CREATE TABLE archive.order_items AS 
SELECT * FROM order_items 
WHERE order_id IN (
    SELECT order_id FROM orders 
    WHERE created_at < CURRENT_DATE - INTERVAL '2 years'
)
LIMIT 0;

-- Archive for invoices
CREATE TABLE archive.invoices AS 
SELECT * FROM invoices 
WHERE invoice_date < CURRENT_DATE - INTERVAL '2 years'
LIMIT 0;

-- Archive for invoice_items
CREATE TABLE archive.invoice_items AS 
SELECT * FROM invoice_items 
WHERE invoice_id IN (
    SELECT invoice_id FROM invoices 
    WHERE invoice_date < CURRENT_DATE - INTERVAL '2 years'
)
LIMIT 0;

-- Archive for inventory movements
CREATE TABLE archive.inventory_movements AS 
SELECT * FROM inventory_movements 
WHERE movement_date < CURRENT_DATE - INTERVAL '2 years'
LIMIT 0;

-- Archive for payments
CREATE TABLE archive.invoice_payments AS 
SELECT * FROM invoice_payments 
WHERE payment_date < CURRENT_DATE - INTERVAL '2 years'
LIMIT 0;

-- Add indexes to archive tables
CREATE INDEX idx_archive_orders_created ON archive.orders(created_at);
CREATE INDEX idx_archive_orders_customer ON archive.orders(customer_id);
CREATE INDEX idx_archive_invoices_date ON archive.invoices(invoice_date);
CREATE INDEX idx_archive_invoices_customer ON archive.invoices(customer_id);

-- Create archive summary view
CREATE VIEW archive.summary AS
SELECT 
    'orders' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM archive.orders
UNION ALL
SELECT 
    'invoices' as table_name,
    COUNT(*) as record_count,
    MIN(invoice_date) as oldest_record,
    MAX(invoice_date) as newest_record
FROM archive.invoices;

COMMENT ON SCHEMA archive IS 'Archive schema for historical data older than 2 years';