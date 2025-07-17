"""
Quick script to check actual database schema for inventory tables
"""
import os
from sqlalchemy import create_engine, text
from api.core.config import settings

# Get database URL
DATABASE_URL = str(settings.DATABASE_URL)
engine = create_engine(DATABASE_URL)

print("Checking inventory table schemas...")

# Check batches table
with engine.connect() as conn:
    print("\n=== BATCHES TABLE ===")
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'batches'
        ORDER BY ordinal_position
    """))
    
    for row in result:
        print(f"{row[0]}: {row[1]} (nullable: {row[2]})")
    
    print("\n=== INVENTORY_MOVEMENTS TABLE ===")
    result = conn.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'inventory_movements'
        ORDER BY ordinal_position
    """))
    
    for row in result:
        print(f"{row[0]}: {row[1]} (nullable: {row[2]})")
    
    print("\n=== PRODUCTS TABLE (inventory columns) ===")
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'products'
        AND column_name IN ('price', 'purchase_price', 'minimum_stock_level', 'reorder_level')
        ORDER BY column_name
    """))
    
    for row in result:
        print(f"{row[0]}: {row[1]}")