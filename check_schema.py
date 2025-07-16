#!/usr/bin/env python3
"""
Check actual database schema to align with SQLAlchemy models
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = "postgresql://postgres.xfytbzavuvpbmxkhqvkb:I5ejcC77brqe4EPY@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

def get_table_schema(table_name):
    """Get column information for a table"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get column information
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = %s 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        cursor.execute(query, (table_name,))
        columns = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return columns
    except Exception as e:
        print(f"Error getting schema for {table_name}: {e}")
        return []

def main():
    # Key tables to check
    tables = ['batches', 'products', 'customers', 'orders', 'order_items', 'users']
    
    for table in tables:
        print(f"\n{'='*50}")
        print(f"TABLE: {table}")
        print(f"{'='*50}")
        
        columns = get_table_schema(table)
        if columns:
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                
                print(f"  {col['column_name']:<30} {col['data_type']}{max_len:<20} {nullable} {default}")
        else:
            print("  Table not found or empty")

if __name__ == "__main__":
    main()