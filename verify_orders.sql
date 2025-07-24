-- Verify orders are being saved correctly
-- Run this in your Supabase SQL Editor

-- Check latest orders
SELECT 
    order_id, 
    order_number, 
    customer_id,
    final_amount,
    created_at,
    order_status
FROM orders 
ORDER BY created_at DESC 
LIMIT 10;

-- Check if order 71 exists specifically
SELECT * FROM orders WHERE order_id = 71;

-- Check orders created today
SELECT * FROM orders 
WHERE DATE(created_at) = CURRENT_DATE 
ORDER BY created_at DESC;

-- Verify order-invoice relationship
SELECT 
    o.order_id,
    o.order_number,
    o.final_amount as order_amount,
    i.invoice_id,
    i.invoice_number,
    i.total_amount as invoice_amount,
    o.created_at
FROM orders o
JOIN invoices i ON o.order_id = i.order_id
ORDER BY o.created_at DESC
LIMIT 5;