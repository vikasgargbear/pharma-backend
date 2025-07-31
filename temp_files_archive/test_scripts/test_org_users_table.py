"""
Test if org_users table exists and has data
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ No database URL found in environment variables")
    exit(1)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if org_users table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'org_users'
        );
    """)
    
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        print("✅ org_users table exists!")
        
        # Get table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'org_users'
            ORDER BY ordinal_position;
        """)
        
        print("\n📋 Table structure:")
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'(nullable)' if col[2] == 'YES' else '(required)'}")
        
        # Count rows
        cur.execute("SELECT COUNT(*) FROM org_users;")
        count = cur.fetchone()[0]
        print(f"\n📊 Total rows: {count}")
        
        # Sample data
        if count > 0:
            cur.execute("""
                SELECT user_id, full_name, email, role, is_active 
                FROM org_users 
                LIMIT 5;
            """)
            rows = cur.fetchall()
            print("\n👥 Sample users:")
            for row in rows:
                print(f"  - ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}, Active: {row[4]}")
    else:
        print("❌ org_users table does NOT exist!")
        print("\n💡 You need to run the Supabase migration scripts to create the table.")
        print("   Check: pharma-backend/database/supabase/01_core_schema.sql")
        
        # Check if users table exists instead
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        if cur.fetchone()[0]:
            print("\n⚠️  Found 'users' table instead of 'org_users'")
            print("   Your database might be using the old schema.")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database connection error: {e}")
    print("\n💡 Make sure your database is running and DATABASE_URL is correct")