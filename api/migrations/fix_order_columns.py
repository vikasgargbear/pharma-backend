"""
Quick fix to add missing total_amount column
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def fix_missing_columns(db: Session) -> dict:
    """Add missing critical columns"""
    try:
        # Add total_amount to orders if missing
        db.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS total_amount DECIMAL(12,2) DEFAULT 0
        """))
        
        # Update total_amount from subtotal + tax - discount
        db.execute(text("""
            UPDATE orders 
            SET total_amount = COALESCE(subtotal_amount, 0) + 
                              COALESCE(tax_amount, 0) - 
                              COALESCE(discount_amount, 0)
            WHERE total_amount = 0 OR total_amount IS NULL
        """))
        
        # Add order_status if missing
        db.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS order_status VARCHAR(20) DEFAULT 'pending'
        """))
        
        # Add paid_amount if missing
        db.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS paid_amount DECIMAL(12,2) DEFAULT 0
        """))
        
        db.commit()
        
        return {
            "success": True,
            "message": "Fixed missing columns successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing columns: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to fix columns: {str(e)}"
        }