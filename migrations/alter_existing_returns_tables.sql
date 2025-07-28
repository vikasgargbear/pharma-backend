-- Alter existing sales_returns table to add missing columns
ALTER TABLE sales_returns 
ADD COLUMN IF NOT EXISTS org_id UUID,
ADD COLUMN IF NOT EXISTS return_number VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS original_sale_id INTEGER,
ADD COLUMN IF NOT EXISTS party_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS subtotal_amount DECIMAL(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS tax_amount DECIMAL(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_amount DECIMAL(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(50) DEFAULT 'credit',
ADD COLUMN IF NOT EXISTS return_status VARCHAR(50) DEFAULT 'completed',
ADD COLUMN IF NOT EXISTS credit_note_no VARCHAR(50),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Change return_id to UUID if it's currently integer
-- This is tricky, so we'll create a new table and migrate data
CREATE TABLE IF NOT EXISTS sale_returns (
    return_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    return_number VARCHAR(50) UNIQUE NOT NULL,
    return_date DATE NOT NULL,
    original_sale_id INTEGER,
    party_id VARCHAR(100),
    reason VARCHAR(50),
    custom_reason TEXT,
    notes TEXT,
    subtotal_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    payment_mode VARCHAR(50) DEFAULT 'credit',
    return_status VARCHAR(50) DEFAULT 'completed',
    credit_note_no VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- Create sale_return_items if it doesn't exist
CREATE TABLE IF NOT EXISTS sale_return_items (
    return_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID NOT NULL REFERENCES sale_returns(return_id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    original_sale_item_id UUID,
    batch_id UUID,
    quantity DECIMAL(15,3) NOT NULL,
    rate DECIMAL(15,2) NOT NULL,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    reason VARCHAR(50),
    custom_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drop the old sales_returns table if it exists and has no important data
-- CAUTION: Only run this if you're sure there's no important data
-- DROP TABLE IF EXISTS sales_returns CASCADE;

-- Rename sale_returns to sales_returns to match existing convention
-- ALTER TABLE sale_returns RENAME TO sales_returns;