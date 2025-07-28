-- Create purchase_returns table
CREATE TABLE IF NOT EXISTS purchase_returns (
    return_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    return_number VARCHAR(50) UNIQUE NOT NULL,
    return_date DATE NOT NULL,
    original_purchase_id INTEGER,
    supplier_id VARCHAR(100),
    reason VARCHAR(50),
    transport_details TEXT,
    notes TEXT,
    subtotal_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    payment_mode VARCHAR(50) DEFAULT 'debit',
    return_status VARCHAR(50) DEFAULT 'completed',
    debit_note_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- Create purchase_return_items table
CREATE TABLE IF NOT EXISTS purchase_return_items (
    return_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID NOT NULL REFERENCES purchase_returns(return_id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    original_purchase_item_id UUID,
    batch_id UUID,
    quantity DECIMAL(15,3) NOT NULL,
    rate DECIMAL(15,2) NOT NULL,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    reason VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_purchase_returns_org_id ON purchase_returns(org_id);
CREATE INDEX idx_purchase_returns_supplier_id ON purchase_returns(supplier_id);
CREATE INDEX idx_purchase_returns_return_date ON purchase_returns(return_date);
CREATE INDEX idx_purchase_returns_original_purchase_id ON purchase_returns(original_purchase_id);
CREATE INDEX idx_purchase_returns_status ON purchase_returns(return_status);

CREATE INDEX idx_purchase_return_items_return_id ON purchase_return_items(return_id);
CREATE INDEX idx_purchase_return_items_product_id ON purchase_return_items(product_id);

-- Add trigger to update updated_at
CREATE TRIGGER update_purchase_returns_updated_at BEFORE UPDATE
    ON purchase_returns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();