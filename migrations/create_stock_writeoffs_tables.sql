-- Create stock_writeoffs table
CREATE TABLE IF NOT EXISTS stock_writeoffs (
    writeoff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    writeoff_number VARCHAR(50) UNIQUE NOT NULL,
    writeoff_date DATE NOT NULL,
    writeoff_type VARCHAR(50) NOT NULL, -- 'expired', 'damaged', 'lost', 'quality_issue', 'other'
    reason TEXT,
    subtotal_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    itc_reversal_amount DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'completed',
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID
);

-- Create stock_writeoff_items table
CREATE TABLE IF NOT EXISTS stock_writeoff_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    writeoff_id UUID NOT NULL REFERENCES stock_writeoffs(writeoff_id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    batch_id UUID,
    batch_number VARCHAR(50),
    expiry_date DATE,
    quantity DECIMAL(15,3) NOT NULL,
    cost_price DECIMAL(15,2) NOT NULL,
    tax_percent DECIMAL(5,2) DEFAULT 0,
    itc_reversal_percent DECIMAL(5,2) DEFAULT 0,
    itc_reversal_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GST adjustment entries table for ITC reversal tracking
CREATE TABLE IF NOT EXISTS gst_adjustments (
    adjustment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    adjustment_date DATE NOT NULL,
    adjustment_type VARCHAR(50) NOT NULL, -- 'itc_reversal', 'credit_note', 'debit_note'
    reference_type VARCHAR(50), -- 'stock_writeoff', 'sale_return', 'purchase_return'
    reference_id UUID,
    cgst_amount DECIMAL(15,2) DEFAULT 0,
    sgst_amount DECIMAL(15,2) DEFAULT 0,
    igst_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    description TEXT,
    gstr_period VARCHAR(7), -- 'YYYY-MM' format for GSTR filing period
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_stock_writeoffs_org_id ON stock_writeoffs(org_id);
CREATE INDEX idx_stock_writeoffs_writeoff_date ON stock_writeoffs(writeoff_date);
CREATE INDEX idx_stock_writeoffs_writeoff_type ON stock_writeoffs(writeoff_type);
CREATE INDEX idx_stock_writeoffs_status ON stock_writeoffs(status);

CREATE INDEX idx_stock_writeoff_items_writeoff_id ON stock_writeoff_items(writeoff_id);
CREATE INDEX idx_stock_writeoff_items_product_id ON stock_writeoff_items(product_id);
CREATE INDEX idx_stock_writeoff_items_batch_id ON stock_writeoff_items(batch_id);
CREATE INDEX idx_stock_writeoff_items_expiry_date ON stock_writeoff_items(expiry_date);

CREATE INDEX idx_gst_adjustments_org_id ON gst_adjustments(org_id);
CREATE INDEX idx_gst_adjustments_adjustment_type ON gst_adjustments(adjustment_type);
CREATE INDEX idx_gst_adjustments_reference ON gst_adjustments(reference_type, reference_id);
CREATE INDEX idx_gst_adjustments_gstr_period ON gst_adjustments(gstr_period);

-- Add trigger to update updated_at
CREATE TRIGGER update_stock_writeoffs_updated_at BEFORE UPDATE
    ON stock_writeoffs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();