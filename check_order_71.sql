-- Check complete details of order 71
SELECT 
    o.*,
    c.customer_name,
    c.gstin as customer_gstin
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_id = 71;

-- Check order items for order 71
SELECT 
    oi.*,
    p.product_name
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE oi.order_id = 71;