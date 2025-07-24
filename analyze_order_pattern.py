"""
Analyze the pattern of missing orders (46, 47, etc.)
"""
from sqlalchemy import create_engine, text
from api.core.config import settings
import json

# Create database connection
engine = create_engine(settings.DATABASE_URL)

print("=== ANALYZING ORDER PATTERN ISSUE ===\n")

with engine.connect() as conn:
    # 1. Check the highest order ID
    result = conn.execute(text("SELECT MAX(order_id) as max_id FROM orders")).fetchone()
    max_order_id = result.max_id if result else 0
    print(f"1. Highest order ID in database: {max_order_id}")
    
    # 2. Check for gaps in order IDs
    print("\n2. Checking for gaps in order IDs:")
    result = conn.execute(text("""
        SELECT order_id FROM orders ORDER BY order_id
    """))
    
    order_ids = [row[0] for row in result]
    expected_id = order_ids[0] if order_ids else 1
    gaps = []
    
    for order_id in order_ids:
        while expected_id < order_id:
            gaps.append(expected_id)
            expected_id += 1
        expected_id += 1
    
    if gaps:
        print(f"   Found {len(gaps)} missing order IDs: {gaps[-10:]}")  # Show last 10
    else:
        print("   No gaps found in order IDs")
    
    # 3. Check if there's a sequence or auto-increment issue
    print("\n3. Checking database sequence:")
    try:
        # PostgreSQL sequence check
        result = conn.execute(text("""
            SELECT last_value, is_called 
            FROM orders_order_id_seq
        """)).fetchone()
        
        if result:
            print(f"   Sequence last_value: {result[0]}, is_called: {result[1]}")
            if result[0] > max_order_id:
                print(f"   ⚠️  SEQUENCE MISMATCH: Sequence is at {result[0]} but max order_id is {max_order_id}")
    except Exception as e:
        print(f"   Could not check sequence: {e}")
    
    # 4. Check recent failed transactions
    print("\n4. Recent orders (last 10):")
    result = conn.execute(text("""
        SELECT order_id, order_number, created_at, order_status
        FROM orders 
        ORDER BY order_id DESC
        LIMIT 10
    """))
    
    for row in result:
        print(f"   ID: {row[0]}, Number: {row[1]}, Created: {row[2]}, Status: {row[3]}")
    
    # 5. Check if orders 46 and 47 ever existed
    print("\n5. Checking audit/history for orders 46-47:")
    for order_id in [46, 47]:
        # Check if there's any reference to these orders
        result = conn.execute(text("""
            SELECT COUNT(*) FROM order_items WHERE order_id = :order_id
        """), {"order_id": order_id}).scalar()
        
        if result > 0:
            print(f"   Found {result} order_items for order {order_id} (order was deleted?)")
        else:
            print(f"   No order_items found for order {order_id}")

print("\n=== ANALYSIS COMPLETE ===")
print("\nLikely causes:")
print("1. Frontend is caching or hardcoding order IDs")
print("2. Frontend is incrementing order IDs locally instead of using server response")
print("3. Database sequence jumped ahead due to failed transactions")
print("4. Orders were created but rolled back due to errors")
print("\nRecommendation:")
print("- Frontend should NEVER generate or assume order IDs")
print("- Always use the order_id returned from the server after creation")
print("- Check frontend code for any localStorage/sessionStorage of order IDs")