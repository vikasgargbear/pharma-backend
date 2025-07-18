"""
Migration script to add drug schedule fields to Product model and create Cart models.
"""
import os
import sys

# Add parent directory to path to import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

def run_migration():
    """
    Run the migration to add drug schedule fields to Product table
    and create Cart and CartItem tables.
    """
    print("Starting migration: Add drug schedule fields to Product and create Cart models")
    
    # Connect to the database
    conn = engine.connect()
    
    try:
        # Add drug schedule fields to Product table
        print("Adding drug schedule fields to Product table...")
        # SQLite doesn't support adding multiple columns in one statement
        conn.execute("ALTER TABLE products ADD COLUMN drug_schedule VARCHAR(10)")
        conn.execute("ALTER TABLE products ADD COLUMN requires_prescription BOOLEAN DEFAULT FALSE")
        conn.execute("ALTER TABLE products ADD COLUMN controlled_substance BOOLEAN DEFAULT FALSE")
        
        # Create Cart table
        print("Creating Cart table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                cart_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create CartItem table
        print("Creating CartItem table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_item_id VARCHAR(36) PRIMARY KEY,
                cart_id VARCHAR(36) REFERENCES carts(cart_id) ON DELETE CASCADE,
                product_id VARCHAR(36) REFERENCES products(product_id),
                batch_id VARCHAR(36) REFERENCES batches(batch_id),
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.close()
        return False
    
    conn.close()
    return True

if __name__ == "__main__":
    run_migration()
