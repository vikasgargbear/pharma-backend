-- Fix challan_items table structure
-- Add missing product_id column

ALTER TABLE challan_items 
ADD COLUMN IF NOT EXISTS product_id INTEGER;

-- Add foreign key constraint to products table
ALTER TABLE challan_items
ADD CONSTRAINT fk_challan_items_product 
FOREIGN KEY (product_id) REFERENCES products(product_id);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_challan_items_product_id ON challan_items(product_id);