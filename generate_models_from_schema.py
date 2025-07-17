#!/usr/bin/env python3
"""
Generate SQLAlchemy models from the actual database schema
"""

import json
from typing import Dict, List

def map_postgres_type_to_sqlalchemy(pg_type: str) -> str:
    """Map PostgreSQL types to SQLAlchemy types"""
    type_mapping = {
        'integer': 'Integer',
        'bigint': 'BigInteger',
        'smallint': 'SmallInteger',
        'numeric': 'Numeric',
        'text': 'Text',
        'character varying': 'String',
        'varchar': 'String',
        'date': 'Date',
        'timestamp': 'DateTime',
        'timestamp with time zone': 'DateTime',
        'timestamp without time zone': 'DateTime',
        'boolean': 'Boolean',
        'uuid': 'String',  # Using String for UUID
        'jsonb': 'JSON',
        'json': 'JSON',
        'double precision': 'Float',
        'real': 'Float'
    }
    
    # Handle array types
    if pg_type.endswith('[]'):
        return 'JSON'  # Use JSON for array types
    
    # Extract base type
    base_type = pg_type.lower()
    for pg, sa in type_mapping.items():
        if pg in base_type:
            return sa
    
    return 'String'  # Default to String for unknown types

def generate_model_code(table_name: str, columns: List[Dict]) -> str:
    """Generate SQLAlchemy model code for a table"""
    # Convert table name to class name
    class_name = ''.join(word.capitalize() for word in table_name.split('_'))
    
    code = f"class {class_name}(Base):\n"
    code += f'    __tablename__ = "{table_name}"\n\n'
    
    # Process columns
    for col in columns:
        col_name = col['name']
        col_type = col['type']
        nullable = col['nullable']
        default = col['default']
        
        # Map type
        sa_type = map_postgres_type_to_sqlalchemy(col_type)
        
        # Handle numeric precision
        if 'numeric' in col_type and '(' in col_type:
            sa_type = col_type.replace('numeric', 'Numeric')
        elif sa_type == 'String' and '(' in col_type:
            # Extract length for varchar
            try:
                length = col_type.split('(')[1].split(')')[0]
                sa_type = f'String({length})'
            except:
                pass
        
        # Build column definition
        col_def = f"    {col_name} = Column({sa_type}"
        
        # Check if primary key
        if 'nextval' in str(default) and '_seq' in str(default):
            col_def += ", primary_key=True, autoincrement=True"
        elif col_name.endswith('_id') and col_name == f"{table_name[:-1]}_id":
            # Likely primary key
            col_def += ", primary_key=True"
        
        # Add nullable
        if not nullable and 'primary_key=True' not in col_def:
            col_def += ", nullable=False"
        
        # Add defaults
        if default and 'nextval' not in str(default):
            if default == 'CURRENT_TIMESTAMP':
                col_def += ", default=datetime.utcnow"
            elif default in ['true', 'false']:
                col_def += f", default={default.capitalize()}"
            elif '::' in str(default):
                # PostgreSQL cast, extract value
                val = default.split('::')[0].strip("'")
                if val.isdigit():
                    col_def += f", default={val}"
                else:
                    col_def += f', default="{val}"'
        
        col_def += ")\n"
        code += col_def
    
    return code

def main():
    # Load schema
    with open('actual_database_schema.json', 'r') as f:
        data = json.load(f)
    
    schema = data['database_schema']
    
    # Core tables to generate (most important for the app)
    core_tables = [
        'products', 'batches', 'customers', 'orders', 'order_items',
        'users', 'payments', 'suppliers', 'purchases', 'organizations',
        'inventory_movements', 'categories', 'units_of_measure'
    ]
    
    # Generate models file
    models_code = '''"""
SQLAlchemy models generated from actual database schema
Auto-generated to match the existing database exactly
"""

from sqlalchemy import Column, String, Integer, BigInteger, Float, Date, DateTime, ForeignKey, Text, Numeric, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

'''
    
    # Generate models for core tables first
    for table_name in core_tables:
        if table_name in schema:
            print(f"Generating model for {table_name}...")
            models_code += generate_model_code(table_name, schema[table_name])
            models_code += "\n\n"
    
    # Add other important tables
    other_tables = ['org_users', 'org_branches', 'price_lists', 'tax_entries', 
                    'challan_items', 'challans', 'sales_returns']
    
    for table_name in other_tables:
        if table_name in schema:
            print(f"Generating model for {table_name}...")
            models_code += generate_model_code(table_name, schema[table_name])
            models_code += "\n\n"
    
    # Save to file
    output_file = 'api/models_minimal.py'
    with open(output_file, 'w') as f:
        f.write(models_code)
    
    print(f"\n✅ Generated {len(core_tables) + len(other_tables)} models")
    print(f"📄 Saved to {output_file}")
    
    # Generate summary
    print("\n📊 Database Summary:")
    print(f"Total tables: {len(schema)}")
    print(f"Generated models for: {len(core_tables) + len(other_tables)} tables")
    
    # Show sample of what we found
    print("\n🔍 Key findings:")
    if 'products' in schema:
        print(f"- Products table has {len(schema['products'])} columns")
    if 'batches' in schema:
        print(f"- Batches table has {len(schema['batches'])} columns")
        # Check for mfg_date vs manufacturing_date
        batch_cols = [col['name'] for col in schema['batches']]
        if 'manufacturing_date' in batch_cols:
            print("  ✅ Has 'manufacturing_date' column")
        if 'mfg_date' in batch_cols:
            print("  ❌ Has 'mfg_date' column")
    
    print("\n💡 Next steps:")
    print("1. Review api/models_minimal.py")
    print("2. Replace api/models.py with the minimal version")
    print("3. Update api/schemas.py to match")
    print("4. Test endpoints")

if __name__ == "__main__":
    main()