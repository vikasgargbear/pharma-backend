-- =====================================================
-- SCRIPT 02: Archive Old Data (FIXED VERSION)
-- Purpose: Move old data to archive tables
-- Run this AFTER creating archive tables
-- =====================================================

-- PART A: Archive and Delete Data (Run this first)
BEGIN;

-- Archive old orders and related data
WITH archived_orders AS (
    INSERT INTO archive.orders 
    SELECT * FROM orders 
    WHERE created_at < CURRENT_DATE - INTERVAL '2 years'
    RETURNING order_id
)
INSERT INTO archive.order_items
SELECT oi.* FROM order_items oi
INNER JOIN archived_orders ao ON oi.order_id = ao.order_id;

-- Archive old invoices and related data
WITH archived_invoices AS (
    INSERT INTO archive.invoices 
    SELECT * FROM invoices 
    WHERE invoice_date < CURRENT_DATE - INTERVAL '2 years'
    RETURNING invoice_id
)
INSERT INTO archive.invoice_items
SELECT ii.* FROM invoice_items ii
INNER JOIN archived_invoices ai ON ii.invoice_id = ai.invoice_id;

-- Archive old payments
INSERT INTO archive.invoice_payments
SELECT * FROM invoice_payments 
WHERE payment_date < CURRENT_DATE - INTERVAL '2 years';

-- Archive old inventory movements
INSERT INTO archive.inventory_movements
SELECT * FROM inventory_movements 
WHERE movement_date < CURRENT_DATE - INTERVAL '2 years';

-- Delete archived data from main tables
DELETE FROM order_items 
WHERE order_id IN (
    SELECT order_id FROM orders 
    WHERE created_at < CURRENT_DATE - INTERVAL '2 years'
);

DELETE FROM orders 
WHERE created_at < CURRENT_DATE - INTERVAL '2 years';

DELETE FROM invoice_items 
WHERE invoice_id IN (
    SELECT invoice_id FROM invoices 
    WHERE invoice_date < CURRENT_DATE - INTERVAL '2 years'
);

DELETE FROM invoices 
WHERE invoice_date < CURRENT_DATE - INTERVAL '2 years';

DELETE FROM invoice_payments 
WHERE payment_date < CURRENT_DATE - INTERVAL '2 years';

DELETE FROM inventory_movements 
WHERE movement_date < CURRENT_DATE - INTERVAL '2 years';

-- Log the archival
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'DATA_ARCHIVAL',
    'Archived data older than 2 years',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

-- Verify counts
SELECT 
    'Archive Summary:' as message,
    (SELECT COUNT(*) FROM archive.orders) as archived_orders,
    (SELECT COUNT(*) FROM archive.invoices) as archived_invoices,
    (SELECT COUNT(*) FROM archive.invoice_payments) as archived_payments,
    (SELECT COUNT(*) FROM archive.inventory_movements) as archived_movements;

COMMIT;

-- PART B: Vacuum Tables (Run these separately, outside of transaction)
-- Note: VACUUM must be run outside of a transaction block
-- Run each of these commands separately:

/*
VACUUM ANALYZE orders;
VACUUM ANALYZE order_items;
VACUUM ANALYZE invoices;
VACUUM ANALYZE invoice_items;
VACUUM ANALYZE invoice_payments;
VACUUM ANALYZE inventory_movements;
*/

-- PART C: Verify Archive Success
SELECT 
    'Main Tables After Archive' as category,
    'orders' as table_name,
    COUNT(*) as remaining_rows,
    MIN(created_at) as oldest_record
FROM orders
UNION ALL
SELECT 
    'Main Tables After Archive' as category,
    'invoices' as table_name,
    COUNT(*) as remaining_rows,
    MIN(invoice_date) as oldest_record
FROM invoices
UNION ALL
SELECT 
    'Archive Tables' as category,
    'archive.orders' as table_name,
    COUNT(*) as archived_rows,
    MAX(created_at) as newest_archived
FROM archive.orders
UNION ALL
SELECT 
    'Archive Tables' as category,
    'archive.invoices' as table_name,
    COUNT(*) as archived_rows,
    MAX(invoice_date) as newest_archived
FROM archive.invoices;