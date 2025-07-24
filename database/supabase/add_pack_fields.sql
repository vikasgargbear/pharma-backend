-- Backend Database Migration: Add Clear Pack Configuration Fields
-- This migration adds new pack-related fields to the products table
-- while maintaining backward compatibility with existing fields

-- Add new pack configuration columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_input VARCHAR(50);
COMMENT ON COLUMN products.pack_input IS 'User input exactly as entered, e.g., "10*10" or "1*100ML"';

ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_quantity INTEGER;
COMMENT ON COLUMN products.pack_quantity IS 'First number in pack configuration (quantity per unit)';

ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_multiplier INTEGER;
COMMENT ON COLUMN products.pack_multiplier IS 'Second number in pack configuration (units per box or measurement size)';

ALTER TABLE products ADD COLUMN IF NOT EXISTS pack_unit_type VARCHAR(10);
COMMENT ON COLUMN products.pack_unit_type IS 'Unit suffix if present, e.g., "ML", "GM", "MG"';

-- Structured fields for calculations
ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_count INTEGER;
COMMENT ON COLUMN products.unit_count IS 'Number of base units per sale unit';

ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_measurement VARCHAR(20);
COMMENT ON COLUMN products.unit_measurement IS 'Combined measurement with unit, e.g., "100ML", "5GM"';

ALTER TABLE products ADD COLUMN IF NOT EXISTS packages_per_box INTEGER;
COMMENT ON COLUMN products.packages_per_box IS 'Number of primary packages in secondary packaging (box)';

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_products_pack_unit_type ON products(pack_unit_type);
CREATE INDEX IF NOT EXISTS idx_products_pack_quantity ON products(pack_quantity);
CREATE INDEX IF NOT EXISTS idx_products_packages_per_box ON products(packages_per_box);

-- Migrate existing data from pack_type field (if it exists)
-- This is a safe migration that preserves existing data
UPDATE products 
SET 
    pack_input = pack_type,
    -- Parse "10*10" format
    pack_quantity = CASE 
        WHEN pack_type ~ '^\d+\*\d+$' THEN 
            CAST(SPLIT_PART(pack_type, '*', 1) AS INTEGER)
        WHEN pack_type ~ '^\d+\*\d+[A-Za-z]+$' THEN 
            CAST(SUBSTRING(pack_type FROM '^\d+') AS INTEGER)
        ELSE NULL
    END,
    -- Parse second number
    pack_multiplier = CASE 
        WHEN pack_type ~ '^\d+\*\d+$' THEN 
            CAST(SPLIT_PART(pack_type, '*', 2) AS INTEGER)
        WHEN pack_type ~ '^\d+\*(\d+)[A-Za-z]+$' THEN 
            CAST(SUBSTRING(pack_type FROM '\*(\d+)') AS INTEGER)
        ELSE NULL
    END,
    -- Extract unit type
    pack_unit_type = CASE 
        WHEN pack_type ~ '^\d+\*\d+([A-Za-z]+)$' THEN 
            UPPER(SUBSTRING(pack_type FROM '[A-Za-z]+$'))
        ELSE NULL
    END
WHERE pack_type IS NOT NULL 
  AND pack_input IS NULL;

-- Set structured fields based on parsed data
UPDATE products 
SET 
    unit_count = pack_quantity,
    unit_measurement = CASE 
        WHEN pack_unit_type IS NOT NULL AND pack_multiplier IS NOT NULL THEN 
            pack_multiplier || pack_unit_type
        ELSE NULL
    END,
    packages_per_box = CASE 
        WHEN pack_unit_type IS NULL AND pack_multiplier IS NOT NULL THEN 
            pack_multiplier
        ELSE NULL
    END
WHERE pack_quantity IS NOT NULL 
  AND unit_count IS NULL;

-- Note: The old fields (pack_type, pack_size, pack_details) are NOT dropped
-- to maintain backward compatibility. They can be deprecated in a future migration.