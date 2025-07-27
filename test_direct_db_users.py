"""
Direct database test for org_users
"""
import psycopg2
import os
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ No DATABASE_URL found in .env file")
    exit(1)

print("🔍 Direct Database Test for org_users\n")
print("=" * 50)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected to database successfully")
    
    # 1. Check if org_users table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'org_users'
        );
    """)
    table_exists = cur.fetchone()[0]
    print(f"\n📋 org_users table exists: {table_exists}")
    
    if not table_exists:
        print("❌ org_users table does NOT exist!")
        
        # Check for users table
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        users_table_exists = cur.fetchone()[0]
        print(f"\n📋 users table exists: {users_table_exists}")
        
    else:
        # 2. Count users
        cur.execute("SELECT COUNT(*) FROM org_users;")
        count = cur.fetchone()[0]
        print(f"\n📊 Total users in org_users: {count}")
        
        # 3. Get all users with details
        if count > 0:
            cur.execute("""
                SELECT 
                    user_id,
                    org_id,
                    full_name,
                    email,
                    role,
                    department,
                    is_active,
                    created_at
                FROM org_users
                ORDER BY created_at DESC
                LIMIT 10;
            """)
            
            users = cur.fetchall()
            print(f"\n👥 Users in database:")
            print("-" * 80)
            for user in users:
                print(f"ID: {user[0]}, Org: {user[1]}, Name: {user[2]}, Email: {user[3]}, Role: {user[4]}, Active: {user[6]}")
            
        # 4. Check organizations
        cur.execute("SELECT COUNT(*) FROM organizations;")
        org_count = cur.fetchone()[0]
        print(f"\n🏢 Total organizations: {org_count}")
        
        if org_count > 0:
            cur.execute("SELECT org_id, org_name, is_active FROM organizations LIMIT 5;")
            orgs = cur.fetchall()
            print("\nOrganizations:")
            for org in orgs:
                print(f"  - {org[0]}: {org[1]} (Active: {org[2]})")
    
    # 5. Test the exact query the API uses
    print("\n🔍 Testing API query:")
    query = """
        SELECT 
            user_id,
            org_id,
            full_name,
            email,
            phone,
            employee_id,
            role,
            permissions,
            department,
            can_view_reports,
            can_modify_prices,
            can_approve_discounts,
            discount_limit_percent,
            is_active,
            last_login_at,
            created_at
        FROM org_users 
        WHERE 1=1
        ORDER BY full_name 
        LIMIT 100 OFFSET 0
    """
    
    cur.execute(query)
    results = cur.fetchall()
    print(f"Query returned {len(results)} rows")
    
    if len(results) > 0:
        # Convert first result to dict to see structure
        columns = [desc[0] for desc in cur.description]
        first_user = dict(zip(columns, results[0]))
        print("\nFirst user data:")
        print(json.dumps({k: str(v) if v else None for k, v in first_user.items()}, indent=2))
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Database error: {e}")
    print(f"\nError type: {type(e).__name__}")
    
print("\n" + "=" * 50)
print("\nIf no users found, run this SQL in Supabase:")
print("1. Check: SELECT COUNT(*) FROM org_users;")
print("2. Create: Run the CREATE_TEST_USER.sql script")