"""
Debug script to check if Order 47 exists in the database
"""
from sqlalchemy import create_engine, text
from api.core.config import settings
import json

# Create database connection
engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # First, check the table structure
    print("Checking orders table structure:")
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'orders'
        ORDER BY ordinal_position
    """))
    
    columns = result.fetchall()
    print("Columns in orders table:")
    for col in columns:
        print(f"  {col[0]} ({col[1]})")
    
    # Check if order 47 exists using proper column names
    print("\nChecking for order 47:")
    result = conn.execute(text("""
        SELECT * FROM orders 
        WHERE order_id = 47 OR order_number = '47'
        LIMIT 5
    """))
    
    orders = result.fetchall()
    
    if orders:
        print(f"Found {len(orders)} order(s) with ID or number 47:")
        col_names = result.keys()
        for order in orders:
            print("  " + ", ".join([f"{col}={val}" for col, val in zip(col_names, order)]))
    else:
        print("No order with order_id 47 or order_number '47' found in database")
    
    # Check recent orders
    print("\nRecent orders (last 10):")
    result = conn.execute(text("""
        SELECT order_id, order_number, customer_id, final_amount, order_status, created_at
        FROM orders 
        ORDER BY order_id DESC
        LIMIT 10
    """))
    
    for order in result:
        print(f"  Order ID: {order[0]}, Order Number: {order[1]}, Customer: {order[2]}, Total: {order[3]}, Status: {order[4]}, Created: {order[5]}")
    
    # Check if there are any orders with IDs around 47
    print("\nOrders with order_id between 40 and 50:")
    result = conn.execute(text("""
        SELECT order_id, order_number, customer_id, final_amount, order_status, created_at
        FROM orders 
        WHERE order_id BETWEEN 40 AND 50
        ORDER BY order_id
    """))
    
    orders = result.fetchall()
    if orders:
        for order in orders:
            print(f"  Order ID: {order[0]}, Order Number: {order[1]}, Customer: {order[2]}, Total: {order[3]}, Status: {order[4]}, Created: {order[5]}")
    else:
        print("  No orders found with order_id between 40 and 50")