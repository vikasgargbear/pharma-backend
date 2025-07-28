-- Add unit conversion columns to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS pack_unit_quantity INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS sub_unit_quantity INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS purchase_unit VARCHAR(50),
ADD COLUMN IF NOT EXISTS sale_unit VARCHAR(50);

-- Update existing products with default values
UPDATE products 
SET 
    pack_unit_quantity = COALESCE(pack_unit_quantity, 1),
    sub_unit_quantity = COALESCE(sub_unit_quantity, 1),
    purchase_unit = COALESCE(purchase_unit, 'Box'),
    sale_unit = COALESCE(sale_unit, 'Strip')
WHERE pack_unit_quantity IS NULL OR sub_unit_quantity IS NULL;