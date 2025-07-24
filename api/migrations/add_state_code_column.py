"""
Add state_code column to customers table
Required for GST calculations (CGST/SGST vs IGST)
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def add_state_code_column(db: Session):
    """Add state_code column to customers table"""
    try:
        # Add state_code column
        db.execute(text("""
            ALTER TABLE customers 
            ADD COLUMN IF NOT EXISTS state_code VARCHAR(2);
        """))
        
        # Create a mapping of common states to their codes
        state_mappings = {
            'Andhra Pradesh': '28',
            'Arunachal Pradesh': '12',
            'Assam': '18',
            'Bihar': '10',
            'Chhattisgarh': '22',
            'Goa': '30',
            'Gujarat': '24',
            'Haryana': '06',
            'Himachal Pradesh': '02',
            'Jharkhand': '20',
            'Karnataka': '29',
            'Kerala': '32',
            'Madhya Pradesh': '23',
            'Maharashtra': '27',
            'Manipur': '14',
            'Meghalaya': '17',
            'Mizoram': '15',
            'Nagaland': '13',
            'Odisha': '21',
            'Punjab': '03',
            'Rajasthan': '08',
            'Sikkim': '11',
            'Tamil Nadu': '33',
            'Telangana': '36',
            'Tripura': '16',
            'Uttar Pradesh': '09',
            'Uttarakhand': '05',
            'West Bengal': '19',
            'Delhi': '07',
            'Jammu and Kashmir': '01',
            'Ladakh': '38',
            'Chandigarh': '04',
            'Puducherry': '34',
            'Andaman and Nicobar Islands': '35',
            'Dadra and Nagar Haveli and Daman and Diu': '26',
            'Lakshadweep': '31'
        }
        
        # Update existing records with state codes based on state name
        for state_name, state_code in state_mappings.items():
            db.execute(text("""
                UPDATE customers 
                SET state_code = :state_code 
                WHERE LOWER(TRIM(state)) = LOWER(:state_name) 
                AND state_code IS NULL
            """), {"state_code": state_code, "state_name": state_name})
        
        # For Karnataka specifically (as shown in the customer data)
        db.execute(text("""
            UPDATE customers 
            SET state_code = '29' 
            WHERE LOWER(TRIM(state)) = 'karnataka' 
            AND state_code IS NULL
        """))
        
        # Add index for performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_customers_state_code 
            ON customers(state_code);
        """))
        
        db.commit()
        
        # Log summary
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_customers,
                COUNT(state_code) as with_state_code,
                COUNT(*) - COUNT(state_code) as without_state_code
            FROM customers
        """)).first()
        
        logger.info(f"✅ Added state_code column to customers table")
        logger.info(f"   Total customers: {result.total_customers}")
        logger.info(f"   With state code: {result.with_state_code}")
        logger.info(f"   Without state code: {result.without_state_code}")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to add state_code column: {str(e)}")
        raise

if __name__ == "__main__":
    from ...database import SessionLocal
    
    db = SessionLocal()
    try:
        add_state_code_column(db)
        print("✅ State code column added successfully")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()