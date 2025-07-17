"""
Migration to add enterprise order management fields
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def add_order_enterprise_columns(db: Session) -> Dict[str, any]:
    """Add missing columns for enterprise order management"""
    
    results = {
        "tables_checked": [],
        "columns_added": [],
        "errors": [],
        "success": True
    }
    
    try:
        # Define columns needed for orders table
        order_columns = [
            # Missing columns for orders
            ("order_number", "VARCHAR(50)", "UNIQUE"),
            ("order_status", "VARCHAR(20)", "DEFAULT 'pending'"),
            ("delivery_date", "DATE", ""),
            ("order_type", "VARCHAR(20)", "DEFAULT 'sales'"),
            ("payment_terms", "VARCHAR(20)", "DEFAULT 'credit'"),
            ("subtotal_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("discount_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("tax_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("paid_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("delivery_charges", "DECIMAL(12,2)", "DEFAULT 0"),
            ("other_charges", "DECIMAL(12,2)", "DEFAULT 0"),
            ("notes", "TEXT", ""),
            ("billing_name", "VARCHAR(200)", ""),
            ("billing_address", "VARCHAR(500)", ""),
            ("billing_gstin", "VARCHAR(20)", ""),
            ("shipping_name", "VARCHAR(200)", ""),
            ("shipping_address", "VARCHAR(500)", ""),
            ("shipping_phone", "VARCHAR(15)", ""),
            ("confirmed_at", "TIMESTAMP", ""),
            ("delivered_at", "TIMESTAMP", ""),
            ("delivery_notes", "TEXT", ""),
            ("created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
            ("org_id", "UUID", "")
        ]
        
        # Check and add columns to orders table
        existing = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'orders'
        """)).fetchall()
        existing_cols = [row[0] for row in existing]
        
        results["tables_checked"].append("orders")
        
        for col_name, data_type, constraints in order_columns:
            if col_name not in existing_cols:
                try:
                    alter_sql = f"ALTER TABLE orders ADD COLUMN {col_name} {data_type}"
                    if constraints:
                        alter_sql += f" {constraints}"
                    
                    db.execute(text(alter_sql))
                    results["columns_added"].append(f"orders.{col_name}")
                    logger.info(f"Added column orders.{col_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        results["errors"].append(f"orders.{col_name}: {str(e)}")
        
        # Define columns for order_items table
        order_items_columns = [
            ("batch_id", "INTEGER", ""),
            ("unit_price", "DECIMAL(12,2)", "NOT NULL DEFAULT 0"),
            ("discount_percent", "DECIMAL(5,2)", "DEFAULT 0"),
            ("discount_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("tax_percent", "DECIMAL(5,2)", "DEFAULT 0"),
            ("tax_amount", "DECIMAL(12,2)", "DEFAULT 0"),
            ("line_total", "DECIMAL(12,2)", "DEFAULT 0"),
            ("created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP")
        ]
        
        # Check order_items table
        existing = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'order_items'
        """)).fetchall()
        existing_cols = [row[0] for row in existing]
        
        results["tables_checked"].append("order_items")
        
        for col_name, data_type, constraints in order_items_columns:
            if col_name not in existing_cols:
                try:
                    alter_sql = f"ALTER TABLE order_items ADD COLUMN {col_name} {data_type}"
                    if constraints:
                        alter_sql += f" {constraints}"
                    
                    db.execute(text(alter_sql))
                    results["columns_added"].append(f"order_items.{col_name}")
                    logger.info(f"Added column order_items.{col_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        results["errors"].append(f"order_items.{col_name}: {str(e)}")
        
        # Create invoices table if it doesn't exist
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id),
                invoice_number VARCHAR(50) UNIQUE NOT NULL,
                invoice_date DATE NOT NULL,
                pdf_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        results["tables_checked"].append("invoices")
        
        # Create sales_returns table if it doesn't exist
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS sales_returns (
                return_id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(order_id),
                return_date DATE NOT NULL,
                return_reason TEXT,
                return_type VARCHAR(20) NOT NULL,
                return_amount DECIMAL(12,2) NOT NULL,
                refund_method VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        results["tables_checked"].append("sales_returns")
        
        # Add indexes for better performance
        indexes = [
            ("idx_orders_order_number", "orders", "order_number"),
            ("idx_orders_customer_id", "orders", "customer_id"),
            ("idx_orders_order_status", "orders", "order_status"),
            ("idx_orders_order_date", "orders", "order_date"),
            ("idx_order_items_order_id", "order_items", "order_id"),
            ("idx_order_items_product_id", "order_items", "product_id")
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                db.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table_name}({column_name})
                """))
                logger.info(f"Created index {index_name}")
            except Exception as e:
                logger.warning(f"Could not create index {index_name}: {str(e)}")
        
        db.commit()
        
        results["message"] = f"Successfully processed {len(results['tables_checked'])} tables, added {len(results['columns_added'])} columns"
        
    except Exception as e:
        db.rollback()
        results["success"] = False
        results["message"] = f"Migration failed: {str(e)}"
        logger.error(f"Order migration failed: {str(e)}")
    
    return results


def create_sample_order_data(db: Session) -> Dict[str, any]:
    """Create sample orders for testing"""
    
    try:
        # Check if we have customers
        customer_count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if customer_count == 0:
            return {
                "success": False,
                "message": "No customers found. Run customer migration first."
            }
        
        # Check if we have products
        product_count = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        if product_count == 0:
            # Create sample products
            sample_products = [
                ("PARA500", "Paracetamol 500mg", "Cipla", 10.50, 5.0),
                ("AMOX250", "Amoxicillin 250mg", "Sun Pharma", 45.00, 12.0),
                ("DISP10", "Disprin 10 Tablets", "Reckitt", 15.00, 5.0),
                ("CROC120", "Crocin 120ml Syrup", "GSK", 85.00, 12.0),
                ("BCOM50", "B-Complex Tablets", "Mankind", 120.00, 18.0)
            ]
            
            for code, name, mfr, mrp, gst in sample_products:
                db.execute(text("""
                    INSERT INTO products (
                        org_id, product_code, product_name, 
                        manufacturer, mrp, gst_percent, is_active
                    ) VALUES (
                        :org_id, :code, :name, :mfr, :mrp, :gst, true
                    )
                """), {
                    "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                    "code": code, "name": name, "mfr": mfr,
                    "mrp": mrp, "gst": gst
                })
            
            logger.info(f"Created {len(sample_products)} sample products")
        
        # Get customer and product IDs
        customers = db.execute(text("""
            SELECT customer_id, customer_name FROM customers LIMIT 3
        """)).fetchall()
        
        products = db.execute(text("""
            SELECT product_id, product_name, mrp, gst_percent FROM products LIMIT 5
        """)).fetchall()
        
        if not customers or not products:
            return {
                "success": False,
                "message": "Need customers and products to create orders"
            }
        
        # Create sample orders
        orders_created = 0
        
        for i, customer in enumerate(customers):
            # Create an order for each customer
            order_number = f"ORD-20250717-{i+1:04d}"
            
            # Calculate totals
            subtotal = 0
            tax = 0
            
            # Use 2-3 products per order
            selected_products = products[i:i+3] if i < len(products)-2 else products[:3]
            
            for product in selected_products:
                qty = (i + 1) * 10  # Variable quantity
                price = float(product.mrp)
                subtotal += qty * price
                tax += (qty * price * float(product.gst_percent) / 100)
            
            total = subtotal + tax
            
            # Create order
            result = db.execute(text("""
                INSERT INTO orders (
                    org_id, order_number, customer_id, order_date,
                    order_status, order_type, payment_terms,
                    subtotal_amount, tax_amount, total_amount, paid_amount,
                    created_at, updated_at
                ) VALUES (
                    :org_id, :order_number, :customer_id, CURRENT_DATE,
                    :status, 'sales', 'credit',
                    :subtotal, :tax, :total, :paid,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING order_id
            """), {
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                "order_number": order_number,
                "customer_id": customer.customer_id,
                "status": ["confirmed", "invoiced", "delivered"][i],
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "paid": total if i == 2 else 0  # Last order is paid
            })
            
            order_id = result.scalar()
            
            # Add order items
            for j, product in enumerate(selected_products):
                qty = (i + 1) * 10
                price = float(product.mrp)
                tax_amt = price * float(product.gst_percent) / 100
                line_total = qty * (price + tax_amt)
                
                db.execute(text("""
                    INSERT INTO order_items (
                        order_id, product_id, quantity,
                        unit_price, tax_percent, tax_amount, line_total
                    ) VALUES (
                        :order_id, :product_id, :quantity,
                        :price, :tax_pct, :tax_amt, :total
                    )
                """), {
                    "order_id": order_id,
                    "product_id": product.product_id,
                    "quantity": qty,
                    "price": price,
                    "tax_pct": product.gst_percent,
                    "tax_amt": tax_amt * qty,
                    "total": line_total
                })
            
            orders_created += 1
            logger.info(f"Created order {order_number} for {customer.customer_name}")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Created {orders_created} sample orders with items"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample orders: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to create sample orders: {str(e)}"
        }