"""
Add multiple address fields to customers table
"""
from sqlalchemy import text

def upgrade(db):
    """Add address_line1, address_line2, and area fields"""
    
    # First, rename existing address to address_line1
    db.execute(text("""
        ALTER TABLE customers 
        RENAME COLUMN address TO address_line1
    """))
    
    # Add new columns
    db.execute(text("""
        ALTER TABLE customers
        ADD COLUMN IF NOT EXISTS address_line2 TEXT,
        ADD COLUMN IF NOT EXISTS area TEXT
    """))
    
    # Update existing data to have area from landmark if available
    db.execute(text("""
        UPDATE customers
        SET area = landmark
        WHERE landmark IS NOT NULL AND area IS NULL
    """))
    
    db.commit()
    print("✓ Added address_line1, address_line2, and area fields to customers table")

def downgrade(db):
    """Revert to single address field"""
    
    # Combine address fields back into one
    db.execute(text("""
        UPDATE customers
        SET address_line1 = COALESCE(address_line1, '') || 
                           CASE WHEN address_line2 IS NOT NULL THEN ', ' || address_line2 ELSE '' END ||
                           CASE WHEN area IS NOT NULL THEN ', ' || area ELSE '' END
    """))
    
    # Rename back to address
    db.execute(text("""
        ALTER TABLE customers 
        RENAME COLUMN address_line1 TO address
    """))
    
    # Drop the new columns
    db.execute(text("""
        ALTER TABLE customers
        DROP COLUMN IF EXISTS address_line2,
        DROP COLUMN IF EXISTS area
    """))
    
    db.commit()
    print("✓ Reverted to single address field")