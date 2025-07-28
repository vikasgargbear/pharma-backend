-- Create sale_returns table
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

-- Create sale_return_items table
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

-- Create indexes
CREATE INDEX idx_sale_returns_org_id ON sale_returns(org_id);
CREATE INDEX idx_sale_returns_party_id ON sale_returns(party_id);
CREATE INDEX idx_sale_returns_return_date ON sale_returns(return_date);
CREATE INDEX idx_sale_returns_original_sale_id ON sale_returns(original_sale_id);
CREATE INDEX idx_sale_returns_status ON sale_returns(return_status);

CREATE INDEX idx_sale_return_items_return_id ON sale_return_items(return_id);
CREATE INDEX idx_sale_return_items_product_id ON sale_return_items(product_id);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sale_returns_updated_at BEFORE UPDATE
    ON sale_returns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();