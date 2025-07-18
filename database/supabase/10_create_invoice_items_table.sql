-- Create invoice_items table if it doesn't exist

CREATE TABLE IF NOT EXISTS invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    
    -- Product details
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(50),
    hsn_code VARCHAR(20),
    batch_number VARCHAR(50),
    
    -- Quantity and pricing
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    
    -- Discounts
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    
    -- Tax details
    tax_percent DECIMAL(5,2) DEFAULT 0,
    cgst_amount DECIMAL(10,2) DEFAULT 0,
    sgst_amount DECIMAL(10,2) DEFAULT 0,
    igst_amount DECIMAL(10,2) DEFAULT 0,
    
    -- Totals
    line_total DECIMAL(12,2) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_product_id ON invoice_items(product_id);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_invoice_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_invoice_items_updated_at_trigger ON invoice_items;
CREATE TRIGGER update_invoice_items_updated_at_trigger
BEFORE UPDATE ON invoice_items
FOR EACH ROW
EXECUTE FUNCTION update_invoice_items_updated_at();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Successfully created invoice_items table';
END $$;