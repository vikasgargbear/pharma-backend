-- =============================================
-- FIX: Supplier Outstanding Trigger
-- =============================================
-- This fixes the goods receipt error by adding the missing constraint
-- =============================================

-- Add unique constraint on purchase_id for ON CONFLICT to work
ALTER TABLE supplier_outstanding 
ADD CONSTRAINT supplier_outstanding_purchase_id_key UNIQUE (purchase_id);

-- Also update the function to handle the case better
CREATE OR REPLACE FUNCTION create_supplier_outstanding_on_purchase()
RETURNS TRIGGER AS $$
BEGIN
    -- Create outstanding when purchase is received
    IF NEW.purchase_status = 'received' AND OLD.purchase_status != 'received' THEN
        -- First check if entry already exists
        IF EXISTS (SELECT 1 FROM supplier_outstanding WHERE purchase_id = NEW.purchase_id) THEN
            -- Update existing entry
            UPDATE supplier_outstanding
            SET 
                outstanding_amount = NEW.final_amount - NEW.paid_amount,
                total_amount = NEW.final_amount,
                updated_at = CURRENT_TIMESTAMP
            WHERE purchase_id = NEW.purchase_id;
        ELSE
            -- Create new entry
            INSERT INTO supplier_outstanding (
                org_id, supplier_id, purchase_id,
                invoice_number, invoice_date,
                total_amount, outstanding_amount,
                due_date, status
            ) VALUES (
                NEW.org_id, NEW.supplier_id, NEW.purchase_id,
                NEW.supplier_invoice_number, NEW.supplier_invoice_date,
                NEW.final_amount, NEW.final_amount - COALESCE(NEW.paid_amount, 0),
                COALESCE(NEW.payment_due_date, NEW.purchase_date + INTERVAL '30 days'),
                'pending'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Supplier outstanding trigger fixed! Goods receipt should now work completely.';
END $$;