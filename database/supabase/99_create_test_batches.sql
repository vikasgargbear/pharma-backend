-- Create test batches for existing products
-- This script creates sample batches to test the stock display

-- Get the default org_id
DO $$
DECLARE
    v_org_id UUID := '12de5e22-eee7-4d25-b3a7-d16d01c6170f';
    v_product RECORD;
    v_batch_number TEXT;
BEGIN
    -- Loop through all products and create batches if they don't exist
    FOR v_product IN 
        SELECT product_id, product_name, product_code 
        FROM products 
        WHERE org_id = v_org_id
    LOOP
        -- Check if product already has batches
        IF NOT EXISTS (
            SELECT 1 FROM batches 
            WHERE product_id = v_product.product_id 
            AND org_id = v_org_id
        ) THEN
            -- Generate batch number
            v_batch_number := v_product.product_code || '-' || TO_CHAR(CURRENT_DATE, 'YYYYMM') || '-001';
            
            -- Create a test batch
            INSERT INTO batches (
                org_id,
                product_id,
                batch_number,
                manufacturing_date,
                expiry_date,
                quantity_received,
                quantity_available,
                quantity_sold,
                cost_price,
                selling_price,
                mrp,
                batch_status,
                created_at,
                updated_at
            ) VALUES (
                v_org_id,
                v_product.product_id,
                v_batch_number,
                CURRENT_DATE - INTERVAL '30 days',
                CURRENT_DATE + INTERVAL '2 years',
                100,  -- quantity_received
                100,  -- quantity_available
                0,    -- quantity_sold
                20.00,  -- cost_price
                25.00,  -- selling_price
                30.00,  -- mrp
                'active',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
            
            RAISE NOTICE 'Created batch % for product %', v_batch_number, v_product.product_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Test batch creation completed';
END $$;

-- Verify batches were created
SELECT 
    p.product_name,
    COUNT(b.batch_id) as batch_count,
    SUM(b.quantity_available) as total_stock
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id
WHERE p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
GROUP BY p.product_id, p.product_name
ORDER BY p.product_name;