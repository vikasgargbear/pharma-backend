-- Create sale_return_items table to match the existing sales_returns table
CREATE TABLE IF NOT EXISTS sale_return_items (
    return_item_id SERIAL PRIMARY KEY,
    return_id INTEGER NOT NULL REFERENCES sales_returns(return_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    original_sale_item_id INTEGER,
    batch_id INTEGER,
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