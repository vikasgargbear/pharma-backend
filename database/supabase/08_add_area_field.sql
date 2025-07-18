-- Add area field to customers table for better address management
-- This migration adds an area/locality field which is important for Indian addresses

-- Add the area column if it doesn't exist
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS area TEXT;

-- Update existing records to populate area from landmark if available
UPDATE customers
SET area = landmark
WHERE landmark IS NOT NULL 
  AND area IS NULL;

-- Add a comment to document the column
COMMENT ON COLUMN customers.area IS 'Area or locality name for better address identification';

-- Create an index on area for faster searches
CREATE INDEX IF NOT EXISTS idx_customers_area ON customers(area);

-- Create a composite index for area-based searches
CREATE INDEX IF NOT EXISTS idx_customers_area_city ON customers(area, city);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully added area field to customers table';
END $$;