-- Add missing columns to invoices table for billing addresses
-- This fixes the "billing_name column does not exist" error

DO $$
BEGIN
    -- Add billing_name column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='billing_name') THEN
        ALTER TABLE invoices ADD COLUMN billing_name VARCHAR(200) NOT NULL DEFAULT '';
        RAISE NOTICE 'Added billing_name column';
    END IF;

    -- Add billing_address column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='billing_address') THEN
        ALTER TABLE invoices ADD COLUMN billing_address VARCHAR(500) NOT NULL DEFAULT '';
        RAISE NOTICE 'Added billing_address column';
    END IF;

    -- Add billing_city column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='billing_city') THEN
        ALTER TABLE invoices ADD COLUMN billing_city VARCHAR(100) NOT NULL DEFAULT '';
        RAISE NOTICE 'Added billing_city column';
    END IF;

    -- Add billing_state column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='billing_state') THEN
        ALTER TABLE invoices ADD COLUMN billing_state VARCHAR(100) NOT NULL DEFAULT '';
        RAISE NOTICE 'Added billing_state column';
    END IF;

    -- Add billing_pincode column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='billing_pincode') THEN
        ALTER TABLE invoices ADD COLUMN billing_pincode VARCHAR(10) NOT NULL DEFAULT '';
        RAISE NOTICE 'Added billing_pincode column';
    END IF;

    -- Add gst_type column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='gst_type') THEN
        ALTER TABLE invoices ADD COLUMN gst_type VARCHAR(20) NOT NULL DEFAULT 'cgst_sgst';
        RAISE NOTICE 'Added gst_type column';
    END IF;

    -- Add place_of_supply column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='place_of_supply') THEN
        ALTER TABLE invoices ADD COLUMN place_of_supply VARCHAR(2) NOT NULL DEFAULT '29';
        RAISE NOTICE 'Added place_of_supply column';
    END IF;

    -- Add customer_gstin column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='customer_gstin') THEN
        ALTER TABLE invoices ADD COLUMN customer_gstin VARCHAR(20);
        RAISE NOTICE 'Added customer_gstin column';
    END IF;

    -- Add taxable_amount column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='taxable_amount') THEN
        ALTER TABLE invoices ADD COLUMN taxable_amount DECIMAL(12,2) NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added taxable_amount column';
    END IF;

    -- Add total_tax_amount column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='invoices' AND column_name='total_tax_amount') THEN
        ALTER TABLE invoices ADD COLUMN total_tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added total_tax_amount column';
    END IF;

    RAISE NOTICE 'Successfully added all missing invoice columns';
END $$;