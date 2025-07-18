-- =============================================
-- 14. Add Sample Products for Testing Invoice Creation
-- =============================================
-- This migration adds sample products to test invoice functionality
-- Created: 2025-07-18
-- =============================================

-- First, check if we need to add sample data
DO $$
BEGIN
    -- Only add sample data if products table is empty or has very few records
    IF (SELECT COUNT(*) FROM products) < 3 THEN
        RAISE NOTICE 'Adding sample products for testing...';
        
        -- Insert sample products with proper organization reference
        INSERT INTO products (
            org_id, product_code, product_name, generic_name, brand_name,
            manufacturer, category, subcategory,
            base_uom_code, purchase_uom_code, sale_uom_code,
            pack_size, purchase_price, sale_price, mrp,
            hsn_code, gst_percent, cgst_percent, sgst_percent,
            prescription_required, is_active,
            minimum_stock_level, reorder_level,
            created_at, updated_at
        ) VALUES 
        -- Product 1: Paracetamol
        (
            '12de5e22-eee7-4d25-b3a7-d16d01c6170f', -- Default org_id
            'PARA500', 'Paracetamol 500mg', 'Paracetamol', 'Crocin',
            'GSK Pharmaceuticals', 'Analgesic', 'Pain Relief',
            'TAB', 'BOX', 'TAB',
            '10x10', 8.50, 10.00, 12.00,
            '30049099', 12.00, 6.00, 6.00,
            FALSE, TRUE,
            100, 50,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        ),
        -- Product 2: Cough Syrup  
        (
            '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
            'COUGH100', 'Cough Syrup 100ml', 'Dextromethorphan', 'Benadryl',
            'Johnson & Johnson', 'Cough & Cold', 'Syrup',
            'BTL', 'BOX', 'BTL',
            '100ml', 65.00, 78.00, 85.00,
            '30039099', 18.00, 9.00, 9.00,
            FALSE, TRUE,
            50, 25,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        ),
        -- Product 3: Vitamin D3
        (
            '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
            'VITD3', 'Vitamin D3 1000 IU', 'Cholecalciferol', 'Calcirol',
            'Cadila Healthcare', 'Vitamin', 'Supplement',
            'CAP', 'BOX', 'CAP',
            '10x10', 110.00, 135.00, 150.00,
            '30049099', 12.00, 6.00, 6.00,
            FALSE, TRUE,
            75, 40,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (org_id, product_code) DO NOTHING;
        
        RAISE NOTICE 'Sample products added successfully';
        
        -- Now add some sample batches for these products
        INSERT INTO batches (
            org_id, product_id, batch_number, lot_number,
            manufacturing_date, expiry_date,
            quantity_received, quantity_available,
            cost_price, selling_price, mrp,
            location_code, is_active,
            created_at, updated_at
        )
        SELECT 
            '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
            p.product_id,
            CASE 
                WHEN p.product_code = 'PARA500' THEN 'BT240101'
                WHEN p.product_code = 'COUGH100' THEN 'BT240201' 
                WHEN p.product_code = 'VITD3' THEN 'BT240301'
            END,
            CASE 
                WHEN p.product_code = 'PARA500' THEN 'LOT2024001'
                WHEN p.product_code = 'COUGH100' THEN 'LOT2024002'
                WHEN p.product_code = 'VITD3' THEN 'LOT2024003'
            END,
            CURRENT_DATE - INTERVAL '30 days', -- Manufactured 30 days ago
            CURRENT_DATE + INTERVAL '18 months', -- Expires in 18 months
            1000, -- Received
            CASE 
                WHEN p.product_code = 'PARA500' THEN 850
                WHEN p.product_code = 'COUGH100' THEN 920
                WHEN p.product_code = 'VITD3' THEN 750
            END, -- Available
            p.purchase_price,
            p.sale_price,
            p.mrp,
            'A-' || (ROW_NUMBER() OVER())::text,
            TRUE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM products p 
        WHERE p.product_code IN ('PARA500', 'COUGH100', 'VITD3')
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Sample batches added successfully';
        
    ELSE
        RAISE NOTICE 'Products table already has data, skipping sample data insertion';
    END IF;
END $$;

-- Show what we have now
SELECT 
    p.product_id,
    p.product_code,
    p.product_name,
    p.sale_price,
    p.mrp,
    COUNT(b.batch_id) as batch_count,
    SUM(b.quantity_available) as total_stock
FROM products p
LEFT JOIN batches b ON p.product_id = b.product_id
WHERE p.org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
GROUP BY p.product_id, p.product_code, p.product_name, p.sale_price, p.mrp
ORDER BY p.product_id
LIMIT 10;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Sample Products Ready for Invoice Testing ===';
    RAISE NOTICE 'Products available:';
    RAISE NOTICE '1. Paracetamol 500mg (PARA500) - ID: varies';
    RAISE NOTICE '2. Cough Syrup 100ml (COUGH100) - ID: varies';  
    RAISE NOTICE '3. Vitamin D3 1000 IU (VITD3) - ID: varies';
    RAISE NOTICE '';
    RAISE NOTICE 'Each product has sample batches with stock available';
    RAISE NOTICE 'Frontend can now create invoices with real product data';
    RAISE NOTICE '================================================';
END $$;