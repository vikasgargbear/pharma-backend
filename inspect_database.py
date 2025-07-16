#!/usr/bin/env python3
"""
Inspect the actual database schema to understand what tables and columns exist
"""

import os
import json
from urllib.parse import urlparse

# Database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.zsqnogqhvkbgkpqcvqdb:AASOdatabase123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')

def inspect_database():
    """Inspect database schema using psycopg2"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Parse database URL
        parsed = urlparse(DATABASE_URL)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            cursor_factory=RealDictCursor
        )
        
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        
        print("📊 Database Schema Inspection")
        print("=" * 60)
        
        schema_info = {}
        
        for table in tables:
            table_name = table['table_name']
            print(f"\n📋 Table: {table_name}")
            print("-" * 40)
            
            # Get columns for this table
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = cur.fetchall()
            schema_info[table_name] = []
            
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  - {col['column_name']}: {col['data_type']} {nullable} {default}")
                
                schema_info[table_name].append({
                    'name': col['column_name'],
                    'type': col['data_type'],
                    'nullable': col['is_nullable'] == 'YES',
                    'default': col['column_default']
                })
        
        # Save schema info to file
        with open('actual_database_schema.json', 'w') as f:
            json.dump(schema_info, f, indent=2)
            
        print("\n✅ Schema information saved to actual_database_schema.json")
        
        cur.close()
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 not installed")
        print("Creating inspection endpoint instead...")
        
        # Create a simple FastAPI endpoint to inspect schema
        inspection_code = '''
@app.get("/inspect-schema")
async def inspect_schema(db: Session = Depends(get_db)):
    """Inspect all tables and columns in the database"""
    try:
        # Get all tables
        tables_result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        schema_info = {}
        
        for table_row in tables_result:
            table_name = table_row[0]
            
            # Get columns for this table
            columns_result = db.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """), {"table_name": table_name})
            
            schema_info[table_name] = []
            for col in columns_result:
                schema_info[table_name].append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == 'YES',
                    "default": col[3]
                })
        
        return {"database_schema": schema_info}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema inspection failed: {str(e)}")
'''
        print("\nAdd this endpoint to your main.py:")
        print(inspection_code)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_database()