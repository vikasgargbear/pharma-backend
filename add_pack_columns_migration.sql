-- Migration script to add pack configuration columns to products table
-- Run this script in your PostgreSQL/Supabase database to add the missing columns

-- Add pack configuration columns if they don't exist
ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_input TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_quantity INTEGER;
ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_multiplier INTEGER;
ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_unit_type TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_count INTEGER;
ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_measurement TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS packages_per_box INTEGER;

-- Add index on pack_input for faster searches
CREATE INDEX IF NOT EXISTS idx_products_pack_input ON products(pack_input);

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' 
AND column_name IN ('pack_input', 'pack_quantity', 'pack_multiplier', 'pack_unit_type', 'unit_count', 'unit_measurement', 'packages_per_box')
ORDER BY column_name;