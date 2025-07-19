-- Check latest inventory movements
SELECT 
    movement_id,
    movement_date,
    movement_type,
    product_id,
    batch_id,
    quantity_in,
    quantity_out,
    reference_type,
    reference_id,
    reference_number,
    notes
FROM inventory_movements
WHERE movement_type IN ('sales_return', 'stock_damage', 'stock_expiry', 'stock_count', 'stock_adjustment')
ORDER BY movement_id DESC
LIMIT 5;

-- Check batch quantities
SELECT 
    b.batch_id,
    b.batch_number,
    p.product_name,
    b.quantity_available,
    b.quantity_sold,
    b.quantity_returned
FROM batches b
JOIN products p ON b.product_id = p.product_id
WHERE b.batch_id = 4;