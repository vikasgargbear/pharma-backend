"""
Migration to add area column to customers table
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def add_area_column_to_customers(db: Session) -> dict:
    """Add area column to customers table if it doesn't exist"""
    
    try:
        # Check if area column already exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'customers' 
                AND column_name = 'area'
            )
        """))
        
        area_exists = result.scalar()
        
        if area_exists:
            return {
                "success": True,
                "message": "Area column already exists in customers table"
            }
        
        # Add area column
        logger.info("Adding area column to customers table")
        db.execute(text("""
            ALTER TABLE customers 
            ADD COLUMN area VARCHAR(100)
        """))
        
        # Create index on area column for better search performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_customers_area 
            ON customers(area)
        """))
        
        db.commit()
        
        return {
            "success": True,
            "message": "Successfully added area column to customers table"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add area column: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to add area column: {str(e)}"
        }