#!/usr/bin/env python3
"""
Fix batch schema by renaming mfg_date to manufacturing_date
"""

import os
import sys
import requests
from urllib.parse import urlparse

# Database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.zsqnogqhvkbgkpqcvqdb:AASOdatabase123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')

def fix_batch_schema():
    """Fix the batch schema by renaming mfg_date to manufacturing_date"""
    
    print("🔧 Fixing batch schema...")
    
    # Parse the database URL to get connection details
    parsed = urlparse(DATABASE_URL)
    
    # Create connection string for psycopg2
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],  # Remove leading slash
        'user': parsed.username,
        'password': parsed.password
    }
    
    try:
        import psycopg2
        
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Check if mfg_date column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batches' 
            AND column_name = 'mfg_date'
        """)
        
        if cur.fetchone():
            print("✅ Found mfg_date column, renaming to manufacturing_date...")
            
            # Rename the column
            cur.execute("ALTER TABLE batches RENAME COLUMN mfg_date TO manufacturing_date")
            conn.commit()
            
            print("✅ Column renamed successfully!")
        else:
            print("ℹ️  mfg_date column not found, checking for manufacturing_date...")
            
            # Check if manufacturing_date exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'batches' 
                AND column_name = 'manufacturing_date'
            """)
            
            if cur.fetchone():
                print("✅ manufacturing_date column already exists!")
            else:
                print("⚠️  Neither mfg_date nor manufacturing_date found in batches table")
        
        # Show final schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'batches' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Final batches table schema:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} ({'nullable' if row[2] == 'YES' else 'not null'})")
        
        cur.close()
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 not installed, trying alternative method...")
        
        # Try using requests to make HTTP call to a database API endpoint
        try:
            # This would require setting up a custom endpoint, but for now let's skip
            print("⚠️  Cannot connect to database directly. Manual fix needed.")
            print("   Please run this SQL command in your database:")
            print("   ALTER TABLE batches RENAME COLUMN mfg_date TO manufacturing_date;")
            
        except Exception as e:
            print(f"❌ Alternative method failed: {e}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    fix_batch_schema()