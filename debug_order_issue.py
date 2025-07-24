"""Debug why orders are not being created in Supabase"""
import psycopg2
import os
from datetime import datetime

# Your Supabase connection
DATABASE_URL = "postgresql://postgres.xfytbzavuvpbmxkhqvkb:I5ejcC77brqe4EPY@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

def check_order_invoice_mismatch():
    """Check for invoices without matching orders"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=== CHECKING FOR INVOICES WITHOUT ORDERS ===")
    cur.execute("""
        SELECT i.invoice_id, i.invoice_number, i.order_id, i.created_at, i.total_amount
        FROM invoices i
        LEFT JOIN orders o ON i.order_id = o.order_id
        WHERE o.order_id IS NULL
        ORDER BY i.created_at DESC
        LIMIT 10
    """)
    
    orphan_invoices = cur.fetchall()
    if orphan_invoices:
        print(f"\n❌ Found {len(orphan_invoices)} invoices WITHOUT matching orders:")
        for inv in orphan_invoices:
            print(f"   Invoice {inv[1]} references order_id {inv[2]} which DOES NOT EXIST!")
    else:
        print("✅ All invoices have matching orders")
    
    print("\n=== CHECKING MAX ORDER ID ===")
    cur.execute("SELECT MAX(order_id) FROM orders")
    max_order = cur.fetchone()[0]
    print(f"Max order_id in orders table: {max_order}")
    
    cur.execute("SELECT MAX(order_id) FROM invoices")
    max_invoice_order = cur.fetchone()[0]
    print(f"Max order_id referenced in invoices: {max_invoice_order}")
    
    if max_invoice_order and max_order and max_invoice_order > max_order:
        print(f"\n❌ PROBLEM: Invoices reference order_ids up to {max_invoice_order} but orders table only has up to {max_order}")
    
    print("\n=== LATEST ORDERS vs INVOICES ===")
    cur.execute("""
        SELECT 'Order' as type, order_id as id, order_number as number, created_at 
        FROM orders 
        ORDER BY created_at DESC LIMIT 5
    """)
    orders = cur.fetchall()
    
    cur.execute("""
        SELECT 'Invoice' as type, invoice_id as id, invoice_number as number, created_at 
        FROM invoices 
        ORDER BY created_at DESC LIMIT 5
    """)
    invoices = cur.fetchall()
    
    print("\nLatest Orders:")
    for o in orders:
        print(f"  {o[0]} ID: {o[1]}, Number: {o[2]}, Created: {o[3]}")
    
    print("\nLatest Invoices:")
    for i in invoices:
        print(f"  {i[0]} ID: {i[1]}, Number: {i[2]}, Created: {i[3]}")
    
    conn.close()

def test_order_creation():
    """Test if we can manually create an order"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("\n=== TESTING MANUAL ORDER CREATION ===")
    try:
        # Get next order_id
        cur.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM orders")
        next_id = cur.fetchone()[0]
        
        test_order = {
            'org_id': '12de5e22-eee7-4d25-b3a7-d16d01c6170f',
            'order_number': f'TEST{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'customer_id': 33,
            'order_type': 'sales',
            'order_status': 'test',
            'final_amount': 100.00
        }
        
        cur.execute("""
            INSERT INTO orders (org_id, order_number, customer_id, order_type, order_status, 
                               order_date, final_amount, created_at, updated_at)
            VALUES (%(org_id)s, %(order_number)s, %(customer_id)s, %(order_type)s, 
                    %(order_status)s, CURRENT_DATE, %(final_amount)s, NOW(), NOW())
            RETURNING order_id
        """, test_order)
        
        new_order_id = cur.fetchone()[0]
        conn.commit()
        print(f"✅ Successfully created test order with ID: {new_order_id}")
        
        # Clean up
        cur.execute("DELETE FROM orders WHERE order_id = %s", (new_order_id,))
        conn.commit()
        print("✅ Test order cleaned up")
        
    except Exception as e:
        print(f"❌ Failed to create order: {e}")
        conn.rollback()
    
    conn.close()

def check_sequence_issue():
    """Check if there's a sequence/auto-increment issue"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("\n=== CHECKING SEQUENCES ===")
    
    # Check if order_id has auto-increment
    cur.execute("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'orders' AND column_name = 'order_id'
    """)
    
    order_col = cur.fetchone()
    print(f"order_id column: {order_col}")
    
    # Check for sequences
    cur.execute("""
        SELECT schemaname, sequencename, last_value 
        FROM pg_sequences 
        WHERE sequencename LIKE '%order%'
    """)
    
    sequences = cur.fetchall()
    if sequences:
        print("\nOrder-related sequences:")
        for seq in sequences:
            print(f"  {seq[0]}.{seq[1]} = {seq[2]}")
    else:
        print("\n⚠️  No order-related sequences found")
    
    conn.close()

if __name__ == "__main__":
    check_order_invoice_mismatch()
    test_order_creation()
    check_sequence_issue()