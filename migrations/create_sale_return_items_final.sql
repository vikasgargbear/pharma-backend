-- Create sale_return_items table to work with existing sales_returns table
-- This matches the structure expected by the application

CREATE TABLE IF NOT EXISTS sale_return_items (
    return_item_id SERIAL PRIMARY KEY,
    return_id INTEGER NOT NULL REFERENCES sales_returns(return_id) ON DELETE CASCADE,
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sale_return_items_return_id ON sale_return_items(return_id);
CREATE INDEX IF NOT EXISTS idx_sale_return_items_product_id ON sale_return_items(product_id);

-- Add comment to clarify the relationship
COMMENT ON TABLE sale_return_items IS 'Items associated with sales returns. Links to sales_returns table, not return_requests.';