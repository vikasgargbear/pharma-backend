"""
Migration script to convert all UUID primary and foreign keys to auto-incrementing integer IDs.
This is a major schema change that requires careful execution.
"""
import os
import sys

# Add parent directory to path to import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

def run_migration():
    """
    Run the migration to convert all UUID primary and foreign keys to auto-incrementing integer IDs.
    This is a complex migration that requires:
    1. Creating new tables with integer IDs
    2. Copying data from old tables to new tables
    3. Dropping old tables
    4. Renaming new tables to original names
    """
    print("Starting migration: Convert UUID keys to auto-incrementing integer IDs")
    
    # Connect to the database
    conn = engine.connect()
    
    try:
        # Begin transaction
        trans = conn.begin()
        
        # For each table, we need to:
        # 1. Create a new table with _new suffix and integer ID
        # 2. Copy data from old table to new table
        # 3. Drop the old table
        # 4. Rename the new table to the original name
        
        # --- Products Table ---
        print("Migrating Products table...")
        conn.execute("""
            CREATE TABLE products_new (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT,
                manufacturer TEXT,
                product_type TEXT,
                hsn_code TEXT,
                gst_percent NUMERIC(10, 2),
                cgst_percent NUMERIC(10, 2),
                sgst_percent NUMERIC(10, 2),
                igst_percent NUMERIC(10, 2),
                mrp NUMERIC(10, 2),
                sale_price NUMERIC(10, 2),
                drug_schedule VARCHAR(10),
                requires_prescription BOOLEAN DEFAULT FALSE,
                controlled_substance BOOLEAN DEFAULT FALSE,
                generic_name TEXT,
                composition TEXT,
                dosage_instructions TEXT,
                storage_instructions TEXT,
                packer TEXT,
                country_of_origin TEXT,
                model_number TEXT,
                dimensions TEXT,
                weight NUMERIC(10, 2),
                weight_unit VARCHAR(10),
                pack_quantity INTEGER,
                pack_form TEXT,
                is_discontinued BOOLEAN DEFAULT FALSE,
                color TEXT,
                asin TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table to new table
        conn.execute("""
            INSERT INTO products_new (
                product_name, category, manufacturer, product_type, hsn_code,
                gst_percent, cgst_percent, sgst_percent, igst_percent, mrp, sale_price,
                drug_schedule, requires_prescription, controlled_substance,
                generic_name, composition, dosage_instructions, storage_instructions,
                packer, country_of_origin, model_number, dimensions, weight, weight_unit,
                pack_quantity, pack_form, is_discontinued, color, asin, created_at, updated_at
            )
            SELECT
                product_name, category, manufacturer, product_type, hsn_code,
                gst_percent, cgst_percent, sgst_percent, igst_percent, mrp, sale_price,
                drug_schedule, requires_prescription, controlled_substance,
                generic_name, composition, dosage_instructions, storage_instructions,
                packer, country_of_origin, model_number, dimensions, weight, weight_unit,
                pack_quantity, pack_form, is_discontinued, color, asin, created_at, updated_at
            FROM products
        """)
        
        # Create mapping table to map old UUIDs to new integer IDs
        conn.execute("""
            CREATE TABLE product_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES products_new(product_id)
            )
        """)
        
        # Populate the mapping table
        conn.execute("""
            INSERT INTO product_id_map (old_id, new_id)
            SELECT products.product_id, products_new.product_id
            FROM products
            JOIN products_new ON products.product_name = products_new.product_name
                AND products.created_at = products_new.created_at
        """)
        
        # --- Batches Table ---
        print("Migrating Batches table...")
        conn.execute("""
            CREATE TABLE batches_new (
                batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                mfg_date DATE,
                expiry_date DATE NOT NULL,
                purchase_price NUMERIC(10, 2) NOT NULL,
                selling_price NUMERIC(10, 2),
                quantity_available INTEGER NOT NULL,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products_new(product_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping table
        conn.execute("""
            INSERT INTO batches_new (
                product_id, batch_number, mfg_date, expiry_date, purchase_price,
                selling_price, quantity_available, location, created_at, updated_at
            )
            SELECT
                product_id_map.new_id, batches.batch_number, batches.mfg_date, batches.expiry_date, 
                batches.purchase_price, batches.selling_price, batches.quantity_available, 
                batches.location, batches.created_at, batches.updated_at
            FROM batches
            JOIN product_id_map ON batches.product_id = product_id_map.old_id
        """)
        
        # Create batch mapping table
        conn.execute("""
            CREATE TABLE batch_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES batches_new(batch_id)
            )
        """)
        
        # Populate batch mapping table
        conn.execute("""
            INSERT INTO batch_id_map (old_id, new_id)
            SELECT batches.batch_id, batches_new.batch_id
            FROM batches
            JOIN product_id_map ON batches.product_id = product_id_map.old_id
            JOIN batches_new ON batches_new.product_id = product_id_map.new_id
                AND batches.batch_number = batches_new.batch_number
                AND batches.expiry_date = batches_new.expiry_date
        """)
        
        # --- Customers Table ---
        print("Migrating Customers table...")
        conn.execute("""
            CREATE TABLE customers_new (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                gst_number TEXT,
                customer_type TEXT,
                credit_limit NUMERIC(10, 2),
                payment_terms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table to new table
        conn.execute("""
            INSERT INTO customers_new (
                customer_name, contact_person, phone, email, address, city, state,
                gst_number, customer_type, credit_limit, payment_terms, created_at, updated_at
            )
            SELECT
                customer_name, contact_person, phone, email, address, city, state,
                gst_number, customer_type, credit_limit, payment_terms, created_at, updated_at
            FROM customers
        """)
        
        # Create customer mapping table
        conn.execute("""
            CREATE TABLE customer_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES customers_new(customer_id)
            )
        """)
        
        # Populate customer mapping table
        conn.execute("""
            INSERT INTO customer_id_map (old_id, new_id)
            SELECT customers.customer_id, customers_new.customer_id
            FROM customers
            JOIN customers_new ON customers.customer_name = customers_new.customer_name
                AND customers.created_at = customers_new.created_at
        """)
        
        # --- Orders Table ---
        print("Migrating Orders table...")
        conn.execute("""
            CREATE TABLE orders_new (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TIMESTAMP,
                gross_amount NUMERIC(10, 2) NOT NULL,
                discount NUMERIC(10, 2) NOT NULL,
                tax_amount NUMERIC(10, 2) NOT NULL,
                final_amount NUMERIC(10, 2) NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                status TEXT DEFAULT 'placed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers_new(customer_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping table
        conn.execute("""
            INSERT INTO orders_new (
                customer_id, order_date, gross_amount, discount, tax_amount,
                final_amount, payment_status, status, created_at, updated_at
            )
            SELECT
                customer_id_map.new_id, orders.order_date, orders.gross_amount, orders.discount,
                orders.tax_amount, orders.final_amount, orders.payment_status, orders.status,
                orders.created_at, orders.updated_at
            FROM orders
            JOIN customer_id_map ON orders.customer_id = customer_id_map.old_id
        """)
        
        # Create order mapping table
        conn.execute("""
            CREATE TABLE order_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES orders_new(order_id)
            )
        """)
        
        # Populate order mapping table
        conn.execute("""
            INSERT INTO order_id_map (old_id, new_id)
            SELECT orders.order_id, orders_new.order_id
            FROM orders
            JOIN customer_id_map ON orders.customer_id = customer_id_map.old_id
            JOIN orders_new ON orders_new.customer_id = customer_id_map.new_id
                AND orders.order_date = orders_new.order_date
                AND orders.final_amount = orders_new.final_amount
        """)
        
        # --- Order Items Table ---
        print("Migrating Order Items table...")
        conn.execute("""
            CREATE TABLE order_items_new (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                batch_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                total_price NUMERIC(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders_new(order_id),
                FOREIGN KEY (batch_id) REFERENCES batches_new(batch_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping tables
        conn.execute("""
            INSERT INTO order_items_new (
                order_id, batch_id, quantity, unit_price, total_price, created_at, updated_at
            )
            SELECT
                order_id_map.new_id, batch_id_map.new_id, order_items.quantity,
                order_items.unit_price, order_items.total_price, order_items.created_at, order_items.updated_at
            FROM order_items
            JOIN order_id_map ON order_items.order_id = order_id_map.old_id
            JOIN batch_id_map ON order_items.batch_id = batch_id_map.old_id
        """)
        
        # --- Payments Table ---
        print("Migrating Payments table...")
        conn.execute("""
            CREATE TABLE payments_new (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                payment_mode TEXT NOT NULL,
                payment_date TIMESTAMP,
                reference_number TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders_new(order_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping table
        conn.execute("""
            INSERT INTO payments_new (
                order_id, amount, payment_mode, payment_date, reference_number, remarks, created_at, updated_at
            )
            SELECT
                order_id_map.new_id, payments.amount, payments.payment_mode, payments.payment_date,
                payments.reference_number, payments.remarks, payments.created_at, payments.updated_at
            FROM payments
            JOIN order_id_map ON payments.order_id = order_id_map.old_id
        """)
        
        # --- Sales Returns Table ---
        print("Migrating Sales Returns table...")
        conn.execute("""
            CREATE TABLE sales_returns_new (
                return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                return_date TIMESTAMP,
                reason TEXT,
                refund_amount NUMERIC(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders_new(order_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping table
        conn.execute("""
            INSERT INTO sales_returns_new (
                order_id, return_date, reason, refund_amount, created_at, updated_at
            )
            SELECT
                order_id_map.new_id, sales_returns.return_date, sales_returns.reason,
                sales_returns.refund_amount, sales_returns.created_at, sales_returns.updated_at
            FROM sales_returns
            JOIN order_id_map ON sales_returns.order_id = order_id_map.old_id
        """)
        
        # --- Users Table ---
        print("Migrating Users table...")
        conn.execute("""
            CREATE TABLE users_new (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table to new table
        conn.execute("""
            INSERT INTO users_new (
                name, email, role, password_hash, created_at, updated_at
            )
            SELECT
                name, email, role, password_hash, created_at, updated_at
            FROM users
        """)
        
        # Create user mapping table
        conn.execute("""
            CREATE TABLE user_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES users_new(user_id)
            )
        """)
        
        # Populate user mapping table
        conn.execute("""
            INSERT INTO user_id_map (old_id, new_id)
            SELECT users.user_id, users_new.user_id
            FROM users
            JOIN users_new ON users.email = users_new.email
        """)
        
        # --- Carts Table ---
        print("Migrating Carts table...")
        conn.execute("""
            CREATE TABLE carts_new (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table to new table (note: user_id is kept as string for Supabase Auth compatibility)
        conn.execute("""
            INSERT INTO carts_new (
                user_id, created_at, updated_at
            )
            SELECT
                user_id, created_at, updated_at
            FROM carts
        """)
        
        # Create cart mapping table
        conn.execute("""
            CREATE TABLE cart_id_map (
                old_id VARCHAR(36) PRIMARY KEY,
                new_id INTEGER,
                FOREIGN KEY (new_id) REFERENCES carts_new(cart_id)
            )
        """)
        
        # Populate cart mapping table
        conn.execute("""
            INSERT INTO cart_id_map (old_id, new_id)
            SELECT carts.cart_id, carts_new.cart_id
            FROM carts
            JOIN carts_new ON carts.user_id = carts_new.user_id
                AND carts.created_at = carts_new.created_at
        """)
        
        # --- Cart Items Table ---
        print("Migrating Cart Items table...")
        conn.execute("""
            CREATE TABLE cart_items_new (
                cart_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cart_id) REFERENCES carts_new(cart_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products_new(product_id),
                FOREIGN KEY (batch_id) REFERENCES batches_new(batch_id)
            )
        """)
        
        # Copy data from old table to new table using the mapping tables
        conn.execute("""
            INSERT INTO cart_items_new (
                cart_id, product_id, batch_id, quantity, added_at
            )
            SELECT
                cart_id_map.new_id, product_id_map.new_id, 
                CASE WHEN cart_items.batch_id IS NULL THEN NULL ELSE batch_id_map.new_id END,
                cart_items.quantity, cart_items.added_at
            FROM cart_items
            JOIN cart_id_map ON cart_items.cart_id = cart_id_map.old_id
            JOIN product_id_map ON cart_items.product_id = product_id_map.old_id
            LEFT JOIN batch_id_map ON cart_items.batch_id = batch_id_map.old_id
        """)
        
        # --- Drop old tables and rename new tables ---
        print("Dropping old tables and renaming new tables...")
        
        # First drop tables with foreign key constraints
        conn.execute("DROP TABLE IF EXISTS cart_items")
        conn.execute("DROP TABLE IF EXISTS carts")
        conn.execute("DROP TABLE IF EXISTS sales_returns")
        conn.execute("DROP TABLE IF EXISTS payments")
        conn.execute("DROP TABLE IF EXISTS order_items")
        conn.execute("DROP TABLE IF EXISTS orders")
        conn.execute("DROP TABLE IF EXISTS batches")
        conn.execute("DROP TABLE IF EXISTS products")
        conn.execute("DROP TABLE IF EXISTS customers")
        conn.execute("DROP TABLE IF EXISTS users")
        
        # Then rename new tables
        conn.execute("ALTER TABLE cart_items_new RENAME TO cart_items")
        conn.execute("ALTER TABLE carts_new RENAME TO carts")
        conn.execute("ALTER TABLE sales_returns_new RENAME TO sales_returns")
        conn.execute("ALTER TABLE payments_new RENAME TO payments")
        conn.execute("ALTER TABLE order_items_new RENAME TO order_items")
        conn.execute("ALTER TABLE orders_new RENAME TO orders")
        conn.execute("ALTER TABLE batches_new RENAME TO batches")
        conn.execute("ALTER TABLE products_new RENAME TO products")
        conn.execute("ALTER TABLE customers_new RENAME TO customers")
        conn.execute("ALTER TABLE users_new RENAME TO users")
        
        # Drop mapping tables
        conn.execute("DROP TABLE IF EXISTS cart_id_map")
        conn.execute("DROP TABLE IF EXISTS user_id_map")
        conn.execute("DROP TABLE IF EXISTS order_id_map")
        conn.execute("DROP TABLE IF EXISTS batch_id_map")
        conn.execute("DROP TABLE IF EXISTS product_id_map")
        conn.execute("DROP TABLE IF EXISTS customer_id_map")
        
        # Commit the transaction
        trans.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        # Rollback in case of error
        trans.rollback()
        print(f"Error during migration: {e}")
        conn.close()
        return False
    
    conn.close()
    return True

if __name__ == "__main__":
    run_migration()
