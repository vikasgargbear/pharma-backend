-- Add missing columns to existing sales_returns table
ALTER TABLE sales_returns 
ADD COLUMN IF NOT EXISTS org_id UUID DEFAULT '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
ADD COLUMN IF NOT EXISTS return_number VARCHAR(50),
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

-- Create sale_return_items table (doesn't exist yet)
CREATE TABLE IF NOT EXISTS sale_return_items (
    return_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id INTEGER REFERENCES sales_returns(return_id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    original_sale_item_id UUID,
    batch_id UUID,
    quantity DECIMAL(15,3) NOT NULL,
    rate DECIMAL(15,2) NOT NULL,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);