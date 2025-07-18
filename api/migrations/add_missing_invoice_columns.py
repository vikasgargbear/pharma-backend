"""
Add missing columns to invoices table
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def add_missing_invoice_columns(db: Session):
    """Add due_date and invoice_status columns to invoices table"""
    try:
        # Add due_date column
        try:
            db.execute(text("""
                ALTER TABLE invoices 
                ADD COLUMN due_date DATE DEFAULT (CURRENT_DATE + INTERVAL '30 days')
            """))
            db.commit()
            logger.info("✅ Added due_date column to invoices table")
        except Exception as e:
            db.rollback()
            if "already exists" in str(e):
                logger.info("due_date column already exists")
            else:
                raise
        
        # Add invoice_status column
        try:
            db.execute(text("""
                ALTER TABLE invoices 
                ADD COLUMN invoice_status VARCHAR(20) DEFAULT 'generated'
            """))
            db.commit()
            logger.info("✅ Added invoice_status column to invoices table")
        except Exception as e:
            db.rollback()
            if "already exists" in str(e):
                logger.info("invoice_status column already exists")
            else:
                raise
        
        # Add check constraint for invoice_status
        try:
            db.execute(text("""
                ALTER TABLE invoices 
                ADD CONSTRAINT check_invoice_status 
                CHECK (invoice_status IN ('draft', 'generated', 'sent', 'paid', 'partially_paid', 'cancelled'))
            """))
            db.commit()
            logger.info("✅ Added check constraint for invoice_status")
        except Exception as e:
            db.rollback()
            if "already exists" in str(e):
                logger.info("invoice_status check constraint already exists")
            else:
                logger.warning(f"Could not add check constraint: {str(e)}")
        
        return {
            "success": True,
            "message": "Successfully added missing columns to invoices table",
            "columns_added": ["due_date", "invoice_status"]
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add missing columns: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to add missing columns: {str(e)}",
            "columns_added": []
        }

# SQL for manual execution in Supabase
MANUAL_SQL = """
-- Add missing columns to invoices table
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS due_date DATE DEFAULT (CURRENT_DATE + INTERVAL '30 days');

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS invoice_status VARCHAR(20) DEFAULT 'generated';

-- Update existing rows if any
UPDATE invoices 
SET due_date = COALESCE(due_date, invoice_date + INTERVAL '30 days')
WHERE due_date IS NULL;

UPDATE invoices 
SET invoice_status = COALESCE(invoice_status, 'generated')
WHERE invoice_status IS NULL;

-- Add check constraint
ALTER TABLE invoices 
DROP CONSTRAINT IF EXISTS check_invoice_status;

ALTER TABLE invoices 
ADD CONSTRAINT check_invoice_status 
CHECK (invoice_status IN ('draft', 'generated', 'sent', 'paid', 'partially_paid', 'cancelled'));
"""