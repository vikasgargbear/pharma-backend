"""
Migration to add inventory tables for batch tracking and stock movements
This enables enterprise-level inventory management
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def get_existing_tables(db: Session) -> list:
    """Get list of existing tables"""
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """))
    return [row[0] for row in result]


def create_batches_table(db: Session) -> bool:
    """Create batches table for batch tracking"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS batches (
                batch_id SERIAL PRIMARY KEY,
                org_id UUID NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                batch_number VARCHAR(50) NOT NULL,
                manufacturing_date DATE,
                expiry_date DATE NOT NULL,
                
                -- Quantities
                quantity_received INTEGER NOT NULL DEFAULT 0,
                quantity_available INTEGER NOT NULL DEFAULT 0,
                
                -- Pricing
                cost_price DECIMAL(12,2) NOT NULL DEFAULT 0,
                mrp DECIMAL(12,2) NOT NULL DEFAULT 0,
                
                -- Additional info
                supplier_id INTEGER,
                purchase_invoice_number VARCHAR(50),
                location_code VARCHAR(100),
                notes TEXT,
                
                -- Timestamps
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT chk_quantities CHECK (
                    quantity_received >= 0 AND
                    quantity_available >= 0
                ),
                CONSTRAINT chk_prices CHECK (
                    cost_price >= 0 AND
                    mrp >= 0
                ),
                CONSTRAINT uk_batch_product UNIQUE (product_id, batch_number)
            )
        """))
        
        # Create indexes
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_batches_org_id ON batches(org_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_batches_product_id ON batches(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_batches_expiry_date ON batches(expiry_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_batches_location ON batches(location_code)"))
        
        logger.info("Created batches table successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating batches table: {str(e)}")
        return False


def create_inventory_movements_table(db: Session) -> bool:
    """Create inventory_movements table for stock tracking"""
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                movement_id SERIAL PRIMARY KEY,
                org_id UUID NOT NULL,
                product_id INTEGER NOT NULL REFERENCES products(product_id),
                batch_id INTEGER REFERENCES batches(batch_id),
                
                -- Movement details
                movement_type VARCHAR(20) NOT NULL,
                movement_date DATE NOT NULL DEFAULT CURRENT_DATE,
                quantity_in INTEGER,
                quantity_out INTEGER,
                
                -- Reference
                reference_type VARCHAR(20),
                reference_id INTEGER,
                
                -- Additional info
                reason VARCHAR(200),
                notes TEXT,
                performed_by VARCHAR(100),
                
                -- Stock levels
                stock_before INTEGER,
                stock_after INTEGER,
                
                -- Timestamp
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                CONSTRAINT chk_movement_type CHECK (
                    movement_type IN ('purchase', 'sale', 'return', 'adjustment', 'transfer')
                ),
                CONSTRAINT chk_reference_type CHECK (
                    reference_type IN ('order', 'purchase', 'adjustment', 'transfer') OR reference_type IS NULL
                )
            )
        """))
        
        # Create indexes
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_org_id ON inventory_movements(org_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_product_id ON inventory_movements(product_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_batch_id ON inventory_movements(batch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_date ON inventory_movements(movement_date DESC)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_type ON inventory_movements(movement_type)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_movements_reference ON inventory_movements(reference_type, reference_id)"))
        
        logger.info("Created inventory_movements table successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating inventory_movements table: {str(e)}")
        return False


def add_inventory_columns_to_products(db: Session) -> bool:
    """Add inventory-related columns to products table"""
    try:
        # Check existing columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products'
        """))
        existing_columns = [row[0] for row in result]
        
        # Add missing columns
        columns_to_add = [
            ("minimum_stock_level", "INTEGER", ""),
            ("reorder_level", "INTEGER", ""),
            ("lead_time_days", "INTEGER", "DEFAULT 7"),
            ("storage_conditions", "VARCHAR(200)", ""),
            ("handling_instructions", "TEXT", "")
        ]
        
        for column, data_type, constraint in columns_to_add:
            if column not in existing_columns:
                db.execute(text(f"""
                    ALTER TABLE products 
                    ADD COLUMN {column} {data_type} {constraint}
                """))
                logger.info(f"Added column {column} to products table")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding columns to products table: {str(e)}")
        return False


def create_sample_inventory_data(db: Session) -> bool:
    """Create sample batch and movement data"""
    try:
        # Check if we have sample data already
        batch_count = db.execute(text("SELECT COUNT(*) FROM batches")).scalar()
        if batch_count > 0:
            logger.info(f"Batches table already has {batch_count} records")
            return True
        
        # Get some products
        # First check if cost_price column exists
        col_check = db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'products' AND column_name = 'cost_price'
            )
        """)).scalar()
        
        if col_check:
            products = db.execute(text("""
                SELECT product_id, product_name, cost_price 
                FROM products 
                WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
                LIMIT 10
            """)).fetchall()
        else:
            # Use a default price if cost_price doesn't exist
            products = db.execute(text("""
                SELECT product_id, product_name, 10.00 as cost_price 
                FROM products 
                WHERE org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f'
                LIMIT 10
            """)).fetchall()
        
        if not products:
            logger.warning("No products found for sample data")
            return True
        
        # Create batches for each product
        batch_data = [
            {
                "product_id": 1,
                "batch_number": "PARA-2024-001",
                "expiry_date": "2025-12-31",
                "quantity": 1000,
                "cost_price": 2.50,
                "mrp": 5.00,
                "location_code": "Rack A-1"
            },
            {
                "product_id": 1,
                "batch_number": "PARA-2024-002",
                "expiry_date": "2025-03-15",
                "quantity": 500,
                "cost_price": 2.45,
                "mrp": 5.00,
                "location_code": "Rack A-1"
            },
            {
                "product_id": 2,
                "batch_number": "AMOX-2024-001",
                "expiry_date": "2025-08-31",
                "quantity": 800,
                "cost_price": 12.00,
                "mrp": 25.00,
                "location_code": "Rack B-3"
            },
            {
                "product_id": 3,
                "batch_number": "CEFI-2024-001",
                "expiry_date": "2024-12-31",  # Near expiry
                "quantity": 200,
                "cost_price": 45.00,
                "mrp": 85.00,
                "location_code": "Cold Storage"
            },
            {
                "product_id": 4,
                "batch_number": "AZIT-2024-001",
                "expiry_date": "2025-06-30",
                "quantity": 600,
                "cost_price": 35.00,
                "mrp": 60.00,
                "location_code": "Rack C-2"
            }
        ]
        
        # Insert batches
        for batch in batch_data[:min(len(products), 5)]:
            batch["product_id"] = products[batch_data.index(batch)][0]
            
            result = db.execute(text("""
                INSERT INTO batches (
                    org_id, product_id, batch_number, expiry_date,
                    quantity_received, quantity_available, cost_price, mrp, location_code, created_at, updated_at
                ) VALUES (
                    '12de5e22-eee7-4d25-b3a7-d16d01c6170f', :product_id, :batch_number, :expiry_date,
                    :quantity, :quantity, :cost_price, :mrp, :location_code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING batch_id
            """), batch)
            
            batch_id = result.scalar()
            
            # Create initial stock movement
            db.execute(text("""
                INSERT INTO inventory_movements (
                    org_id, product_id, batch_id, movement_type,
                    quantity_in, reference_type, notes, created_at
                ) VALUES (
                    '12de5e22-eee7-4d25-b3a7-d16d01c6170f', :product_id, :batch_id, 'purchase',
                    :quantity_in, 'batch_creation', 'Initial stock entry', CURRENT_TIMESTAMP
                )
            """), {
                "product_id": batch["product_id"],
                "batch_id": batch_id,
                "quantity_in": batch["quantity"]
            })
        
        # Create some sample movements
        db.execute(text("""
            INSERT INTO inventory_movements (
                org_id, product_id, batch_id, movement_type,
                quantity_out, reference_type, reference_id, notes, created_at
            ) 
            SELECT 
                '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
                b.product_id,
                b.batch_id,
                'sale',
                50,
                'order',
                1,
                'Order fulfillment',
                CURRENT_TIMESTAMP
            FROM batches b
            WHERE b.batch_number = 'PARA-2024-001'
        """))
        
        # Update batch quantity
        db.execute(text("""
            UPDATE batches 
            SET quantity_available = quantity_available - 50
            WHERE batch_number = 'PARA-2024-001'
        """))
        
        logger.info("Created sample inventory data")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return False


def add_inventory_enterprise_tables(db: Session) -> Dict[str, Any]:
    """Main migration function to add inventory tables"""
    try:
        logger.info("Starting inventory tables migration...")
        
        # Get existing tables
        existing_tables = get_existing_tables(db)
        logger.info(f"Existing tables: {existing_tables}")
        
        results = {
            "batches_table": False,
            "movements_table": False,
            "product_columns": False,
            "sample_data": False
        }
        
        # Create tables
        if "batches" not in existing_tables:
            results["batches_table"] = create_batches_table(db)
        else:
            logger.info("Batches table already exists")
            results["batches_table"] = True
        
        if "inventory_movements" not in existing_tables:
            results["movements_table"] = create_inventory_movements_table(db)
        else:
            logger.info("Inventory movements table already exists")
            results["movements_table"] = True
        
        # Add columns to products
        results["product_columns"] = add_inventory_columns_to_products(db)
        
        # Create sample data
        results["sample_data"] = create_sample_inventory_data(db)
        
        # Commit if all successful
        if all(results.values()):
            db.commit()
            return {
                "success": True,
                "message": "Inventory tables created successfully",
                "details": results
            }
        else:
            db.rollback()
            return {
                "success": False,
                "message": "Some operations failed",
                "details": results
            }
            
    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {str(e)}")
        return {
            "success": False,
            "message": f"Migration failed: {str(e)}",
            "details": {}
        }