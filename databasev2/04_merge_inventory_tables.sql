-- =====================================================
-- SCRIPT 04: Merge Inventory Tables
-- Purpose: Consolidate all inventory tracking into single table
-- =====================================================

BEGIN;

-- Step 1: Ensure inventory_movements has all necessary columns
ALTER TABLE inventory_movements 
ADD COLUMN IF NOT EXISTS movement_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS reference_id INTEGER,
ADD COLUMN IF NOT EXISTS from_location_id INTEGER,
ADD COLUMN IF NOT EXISTS to_location_id INTEGER,
ADD COLUMN IF NOT EXISTS unit_cost DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS reason TEXT,
ADD COLUMN IF NOT EXISTS created_by INTEGER;

-- Step 2: Migrate data from inventory_transactions if exists
INSERT INTO inventory_movements (
    org_id,
    movement_type,
    movement_date,
    reference_type,
    reference_id,
    product_id,
    batch_id,
    quantity,
    unit_cost,
    from_location_id,
    to_location_id,
    reason,
    created_by,
    created_at
)
SELECT 
    org_id,
    transaction_type as movement_type,
    transaction_date as movement_date,
    reference_type,
    reference_id,
    product_id,
    batch_id,
    quantity,
    unit_cost,
    NULL as from_location_id,
    location_id as to_location_id,
    notes as reason,
    created_by,
    created_at
FROM inventory_transactions
WHERE NOT EXISTS (
    SELECT 1 FROM inventory_movements im 
    WHERE im.reference_type = inventory_transactions.reference_type 
    AND im.reference_id = inventory_transactions.reference_id
);

-- Step 3: Migrate stock transfers
INSERT INTO inventory_movements (
    org_id,
    movement_type,
    movement_date,
    reference_type,
    reference_id,
    product_id,
    batch_id,
    quantity,
    from_location_id,
    to_location_id,
    reason,
    created_by,
    created_at
)
SELECT 
    st.org_id,
    'transfer' as movement_type,
    st.transfer_date as movement_date,
    'stock_transfer' as reference_type,
    st.transfer_id as reference_id,
    sti.product_id,
    sti.batch_id,
    sti.quantity,
    st.from_location_id,
    st.to_location_id,
    st.reason,
    st.created_by,
    st.created_at
FROM stock_transfers st
JOIN stock_transfer_items sti ON st.transfer_id = sti.transfer_id
WHERE NOT EXISTS (
    SELECT 1 FROM inventory_movements im 
    WHERE im.reference_type = 'stock_transfer' 
    AND im.reference_id = st.transfer_id
);

-- Step 4: Create comprehensive inventory status view
CREATE OR REPLACE VIEW current_inventory_status AS
WITH inventory_summary AS (
    SELECT 
        im.org_id,
        im.product_id,
        im.batch_id,
        COALESCE(im.to_location_id, 1) as location_id,
        SUM(CASE 
            WHEN im.movement_type IN ('purchase', 'return_in', 'adjustment_in', 'transfer_in') 
            THEN im.quantity
            WHEN im.movement_type IN ('sale', 'return_out', 'adjustment_out', 'transfer_out', 'writeoff') 
            THEN -im.quantity
            ELSE 0
        END) as current_quantity
    FROM inventory_movements im
    GROUP BY im.org_id, im.product_id, im.batch_id, COALESCE(im.to_location_id, 1)
)
SELECT 
    inv.org_id,
    inv.product_id,
    p.product_name,
    p.product_code,
    inv.batch_id,
    b.batch_number,
    b.expiry_date,
    inv.location_id,
    COALESCE(sl.location_name, 'Main Store') as location_name,
    inv.current_quantity,
    p.reorder_level,
    p.reorder_quantity,
    CASE 
        WHEN inv.current_quantity <= 0 THEN 'out_of_stock'
        WHEN inv.current_quantity < p.reorder_level THEN 'low_stock'
        ELSE 'in_stock'
    END as stock_status,
    b.mrp,
    b.selling_price,
    (inv.current_quantity * b.selling_price) as stock_value
FROM inventory_summary inv
JOIN products p ON inv.product_id = p.product_id
JOIN batches b ON inv.batch_id = b.batch_id
LEFT JOIN storage_locations sl ON inv.location_id = sl.location_id
WHERE inv.current_quantity != 0;

-- Step 5: Create product-level inventory summary
CREATE OR REPLACE VIEW product_inventory_summary AS
SELECT 
    p.org_id,
    p.product_id,
    p.product_code,
    p.product_name,
    p.category_id,
    c.category_name,
    COUNT(DISTINCT b.batch_id) as total_batches,
    SUM(cis.current_quantity) as total_quantity,
    MIN(b.expiry_date) as nearest_expiry,
    AVG(b.mrp) as avg_mrp,
    SUM(cis.stock_value) as total_stock_value,
    CASE 
        WHEN SUM(cis.current_quantity) <= 0 THEN 'out_of_stock'
        WHEN SUM(cis.current_quantity) < p.reorder_level THEN 'low_stock'
        ELSE 'in_stock'
    END as stock_status
FROM products p
LEFT JOIN current_inventory_status cis ON p.product_id = cis.product_id
LEFT JOIN batches b ON cis.batch_id = b.batch_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY p.org_id, p.product_id, p.product_code, p.product_name, 
         p.category_id, c.category_name, p.reorder_level;

-- Step 6: Create inventory movement tracking function
CREATE OR REPLACE FUNCTION track_inventory_movement(
    p_org_id UUID,
    p_movement_type VARCHAR(50),
    p_product_id INTEGER,
    p_batch_id INTEGER,
    p_quantity INTEGER,
    p_reference_type VARCHAR(50),
    p_reference_id INTEGER,
    p_from_location INTEGER DEFAULT NULL,
    p_to_location INTEGER DEFAULT NULL,
    p_user_id INTEGER DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_movement_id INTEGER;
BEGIN
    INSERT INTO inventory_movements (
        org_id,
        movement_type,
        movement_date,
        product_id,
        batch_id,
        quantity,
        reference_type,
        reference_id,
        from_location_id,
        to_location_id,
        created_by,
        created_at
    ) VALUES (
        p_org_id,
        p_movement_type,
        CURRENT_TIMESTAMP,
        p_product_id,
        p_batch_id,
        p_quantity,
        p_reference_type,
        p_reference_id,
        p_from_location,
        p_to_location,
        p_user_id,
        CURRENT_TIMESTAMP
    ) RETURNING movement_id INTO v_movement_id;
    
    RETURN v_movement_id;
END;
$$ LANGUAGE plpgsql;

-- Step 7: Drop old tables (after confirming data migration)
DROP TABLE IF EXISTS inventory_transactions CASCADE;
DROP TABLE IF EXISTS stock_transfer_items CASCADE;
DROP TABLE IF EXISTS stock_transfers CASCADE;
DROP TABLE IF EXISTS batch_inventory_status CASCADE;
DROP TABLE IF EXISTS batch_locations CASCADE;

-- Step 8: Create optimized indexes
CREATE INDEX IF NOT EXISTS idx_inventory_movements_product_batch 
ON inventory_movements(product_id, batch_id);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_reference 
ON inventory_movements(reference_type, reference_id);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_date 
ON inventory_movements(movement_date);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_location 
ON inventory_movements(to_location_id);

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

-- Refresh materialized views if any
-- REFRESH MATERIALIZED VIEW current_inventory_status;