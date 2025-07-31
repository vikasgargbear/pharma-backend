-- =====================================================
-- SCRIPT 04: Merge Inventory Tables (FIXED)
-- Based on actual schema structure
-- =====================================================

BEGIN;

-- Step 1: Check if we need to merge inventory_transactions
DO $$
BEGIN
    -- Only proceed if inventory_transactions exists and has data
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'inventory_transactions' 
               AND table_schema = 'public') THEN
        
        -- Migrate data from inventory_transactions
        INSERT INTO inventory_movements (
            org_id,
            movement_type,
            movement_date,
            reference_type,
            reference_id,
            product_id,
            batch_id,
            quantity_in,
            quantity_out,
            movement_uom,
            from_location,
            to_location,
            performed_by,
            notes,
            created_at
        )
        SELECT 
            b.org_id,
            it.transaction_type,
            it.transaction_date::timestamp with time zone,
            it.reference_type,
            it.reference_id,
            b.product_id,
            it.batch_id,
            CASE WHEN it.quantity_change > 0 THEN it.quantity_change ELSE 0 END,
            CASE WHEN it.quantity_change < 0 THEN ABS(it.quantity_change) ELSE 0 END,
            p.sale_unit,
            NULL,
            NULL,
            it.performed_by,
            it.remarks,
            it.created_at::timestamp with time zone
        FROM inventory_transactions it
        JOIN batches b ON it.batch_id = b.batch_id
        JOIN products p ON b.product_id = p.product_id
        WHERE NOT EXISTS (
            SELECT 1 FROM inventory_movements im 
            WHERE im.reference_type = it.reference_type 
            AND im.reference_id = it.reference_id
            AND im.batch_id = it.batch_id
        );
        
        -- Drop the table after migration
        DROP TABLE inventory_transactions CASCADE;
        RAISE NOTICE 'Migrated and dropped inventory_transactions';
    END IF;
END $$;

-- Step 2: Check and migrate stock_transfers if exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'stock_transfers' 
               AND table_schema = 'public') THEN
        
        -- Check if stock_transfer_items exists
        IF EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_name = 'stock_transfer_items' 
                   AND table_schema = 'public') THEN
            
            -- Migrate stock transfers
            INSERT INTO inventory_movements (
                org_id,
                movement_type,
                movement_date,
                reference_type,
                reference_id,
                product_id,
                batch_id,
                quantity_out,
                quantity_in,
                from_location,
                to_location,
                performed_by,
                notes,
                created_at
            )
            SELECT 
                st.org_id,
                'transfer',
                st.transfer_date::timestamp with time zone,
                'stock_transfer',
                st.transfer_id,
                sti.product_id,
                sti.batch_id,
                COALESCE(sti.received_quantity, sti.approved_quantity, sti.requested_quantity), -- out from source
                COALESCE(sti.received_quantity, sti.approved_quantity, sti.requested_quantity), -- in to destination
                st.from_branch_id::text,
                st.to_branch_id::text,
                st.requested_by,
                st.transfer_reason,
                st.created_at
            FROM stock_transfers st
            JOIN stock_transfer_items sti ON st.transfer_id = sti.transfer_id;
            
            -- Drop tables
            DROP TABLE stock_transfer_items CASCADE;
            DROP TABLE stock_transfers CASCADE;
            RAISE NOTICE 'Migrated and dropped stock_transfers';
        END IF;
    END IF;
END $$;

-- Step 3: Drop other redundant inventory tables if they exist
DROP TABLE IF EXISTS batch_inventory_status CASCADE;
DROP TABLE IF EXISTS batch_locations CASCADE;
DROP TABLE IF EXISTS stock_movements CASCADE;

-- Step 4: Create useful views for inventory analysis
CREATE OR REPLACE VIEW current_inventory_by_batch AS
SELECT 
    im.org_id,
    im.product_id,
    p.product_name,
    p.product_code,
    im.batch_id,
    b.batch_number,
    b.expiry_date,
    SUM(im.quantity_in - im.quantity_out) as current_quantity,
    b.mrp,
    b.selling_price,
    SUM(im.quantity_in - im.quantity_out) * b.selling_price as stock_value
FROM inventory_movements im
JOIN products p ON im.product_id = p.product_id
JOIN batches b ON im.batch_id = b.batch_id
GROUP BY im.org_id, im.product_id, p.product_name, p.product_code, 
         im.batch_id, b.batch_number, b.expiry_date, b.mrp, b.selling_price
HAVING SUM(im.quantity_in - im.quantity_out) > 0;

-- Step 5: Create product-level summary
CREATE OR REPLACE VIEW current_inventory_by_product AS
SELECT 
    p.org_id,
    p.product_id,
    p.product_code,
    p.product_name,
    p.category_id,
    COUNT(DISTINCT b.batch_id) as active_batches,
    SUM(im.quantity_in - im.quantity_out) as total_quantity,
    MIN(b.expiry_date) as nearest_expiry,
    SUM((im.quantity_in - im.quantity_out) * b.selling_price) as total_stock_value
FROM products p
LEFT JOIN inventory_movements im ON p.product_id = im.product_id
LEFT JOIN batches b ON im.batch_id = b.batch_id
GROUP BY p.org_id, p.product_id, p.product_code, p.product_name, p.category_id;

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inventory_movements_product_batch 
ON inventory_movements(product_id, batch_id);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_reference 
ON inventory_movements(reference_type, reference_id);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_date 
ON inventory_movements(movement_date);

-- Log the consolidation
INSERT INTO activity_log (org_id, activity_type, activity_description, created_at)
SELECT 
    org_id,
    'TABLE_CONSOLIDATION',
    'Consolidated inventory tables into unified inventory_movements table',
    CURRENT_TIMESTAMP
FROM organizations
LIMIT 1;

COMMIT;

-- Check final status
SELECT 
    'Inventory consolidation complete' as status,
    COUNT(DISTINCT table_name) as tables_dropped
FROM (
    VALUES ('inventory_transactions'), ('stock_transfers'), ('stock_transfer_items'), 
           ('batch_inventory_status'), ('batch_locations'), ('stock_movements')
) AS t(table_name)
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = t.table_name
);