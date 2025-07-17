"""
Migration to add enterprise customer fields to the database
This is how companies scale - incrementally adding features
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def get_existing_columns(db: Session, table_name: str) -> List[str]:
    """Get list of existing columns in a table"""
    result = db.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """), {"table_name": table_name})
    
    return [row[0] for row in result]

def add_customer_enterprise_columns(db: Session) -> Dict[str, any]:
    """Add missing columns for enterprise customer management"""
    
    results = {
        "checked": 0,
        "added": 0,
        "errors": [],
        "existing_columns": [],
        "new_columns": []
    }
    
    try:
        # Get existing columns
        existing_columns = get_existing_columns(db, "customers")
        results["existing_columns"] = existing_columns
        logger.info(f"Existing columns: {existing_columns}")
        
        # Define all columns we need for enterprise features
        required_columns = [
            # Basic Information
            ("customer_code", "VARCHAR(50)", "UNIQUE"),
            ("contact_person", "VARCHAR(100)", ""),
            ("phone", "VARCHAR(15)", ""),
            ("alternate_phone", "VARCHAR(15)", ""),
            ("email", "VARCHAR(100)", ""),
            
            # Address
            ("address_line1", "VARCHAR(200)", ""),
            ("address_line2", "VARCHAR(200)", ""),
            ("city", "VARCHAR(100)", ""),
            ("state", "VARCHAR(100)", ""),
            ("pincode", "VARCHAR(10)", ""),
            
            # GST and Compliance
            ("gstin", "VARCHAR(20)", ""),
            ("pan_number", "VARCHAR(20)", ""),
            ("drug_license_number", "VARCHAR(50)", ""),
            
            # Business Details
            ("customer_type", "VARCHAR(20)", "DEFAULT 'retail'"),
            ("credit_limit", "DECIMAL(12,2)", "DEFAULT 0"),
            ("credit_days", "INTEGER", "DEFAULT 0"),
            ("discount_percent", "DECIMAL(5,2)", "DEFAULT 0"),
            
            # Status and Metadata
            ("is_active", "BOOLEAN", "DEFAULT true"),
            ("notes", "TEXT", ""),
            ("created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
            
            # Organization
            ("org_id", "UUID", "")
        ]
        
        # Add missing columns
        for column_name, data_type, constraints in required_columns:
            results["checked"] += 1
            
            if column_name not in existing_columns:
                try:
                    # Build ALTER TABLE statement
                    alter_sql = f"ALTER TABLE customers ADD COLUMN {column_name} {data_type}"
                    if constraints:
                        alter_sql += f" {constraints}"
                    
                    logger.info(f"Adding column: {column_name}")
                    db.execute(text(alter_sql))
                    results["added"] += 1
                    results["new_columns"].append(column_name)
                    
                except Exception as e:
                    error_msg = f"Error adding {column_name}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
        
        # Add indexes for better performance
        index_columns = [
            ("idx_customers_org_id", "org_id"),
            ("idx_customers_customer_code", "customer_code"),
            ("idx_customers_phone", "phone"),
            ("idx_customers_gstin", "gstin"),
            ("idx_customers_customer_type", "customer_type"),
            ("idx_customers_is_active", "is_active")
        ]
        
        for index_name, column_name in index_columns:
            if column_name in existing_columns or column_name in results["new_columns"]:
                try:
                    db.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON customers({column_name})
                    """))
                    logger.info(f"Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index {index_name}: {str(e)}")
        
        # Commit all changes
        db.commit()
        
        # Update the updated_at trigger if it doesn't exist
        try:
            db.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))
            
            db.execute(text("""
                DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
                CREATE TRIGGER update_customers_updated_at
                BEFORE UPDATE ON customers
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
            """))
            
            db.commit()
            logger.info("Created updated_at trigger")
            
        except Exception as e:
            logger.warning(f"Could not create trigger: {str(e)}")
        
        results["success"] = True
        results["message"] = f"Successfully added {results['added']} columns to customers table"
        
    except Exception as e:
        db.rollback()
        results["success"] = False
        results["message"] = f"Migration failed: {str(e)}"
        logger.error(f"Migration failed: {str(e)}")
    
    return results

def create_sample_customer_data(db: Session) -> Dict[str, any]:
    """Create sample customer data to test the system"""
    
    try:
        # Check if we already have customers
        count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        
        if count > 0:
            return {
                "success": True,
                "message": f"Customers table already has {count} records"
            }
        
        # Insert sample customers
        sample_customers = [
            {
                "customer_name": "Apollo Pharmacy - MG Road",
                "customer_code": "APO001",
                "contact_person": "Rajesh Kumar",
                "phone": "9876543210",
                "email": "apollo.mgroad@example.com",
                "address_line1": "123 MG Road",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
                "gstin": "29ABCDE1234F1Z5",
                "customer_type": "pharmacy",
                "credit_limit": 50000,
                "credit_days": 30,
                "discount_percent": 5.0
            },
            {
                "customer_name": "MedPlus - Koramangala",
                "customer_code": "MED001",
                "contact_person": "Priya Sharma",
                "phone": "9876543211",
                "email": "medplus.kora@example.com",
                "address_line1": "456 1st Block",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560034",
                "gstin": "29XYZAB5678G2H6",
                "customer_type": "pharmacy",
                "credit_limit": 75000,
                "credit_days": 45,
                "discount_percent": 7.5
            },
            {
                "customer_name": "City Hospital",
                "customer_code": "HOS001",
                "contact_person": "Dr. Amit Patel",
                "phone": "9876543212",
                "email": "purchase@cityhospital.com",
                "address_line1": "789 Hospital Road",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560002",
                "gstin": "29HOSPT9012I3J7",
                "customer_type": "hospital",
                "credit_limit": 200000,
                "credit_days": 60,
                "discount_percent": 10.0
            }
        ]
        
        for customer in sample_customers:
            customer["org_id"] = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"
            
            columns = ", ".join(customer.keys())
            placeholders = ", ".join([f":{key}" for key in customer.keys()])
            
            db.execute(text(f"""
                INSERT INTO customers ({columns})
                VALUES ({placeholders})
            """), customer)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Created {len(sample_customers)} sample customers"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": f"Failed to create sample data: {str(e)}"
        }