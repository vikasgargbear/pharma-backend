-- Check all columns in orders table for recent orders
SELECT * FROM orders 
WHERE order_id IN (71, 70, 69, 62)
ORDER BY order_id DESC;