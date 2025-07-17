#!/usr/bin/env python3
"""
Generate SQLAlchemy models from existing database
This will create models that exactly match the database schema
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.core.schema_inspector import DatabaseSchemaInspector

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.zsqnogqhvkbgkpqcvqdb:AASOdatabase123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')

def main():
    print("🔍 Inspecting database schema...")
    print(f"Database: {DATABASE_URL.split('@')[1]}")
    print("=" * 60)
    
    try:
        # Create inspector
        inspector = DatabaseSchemaInspector(DATABASE_URL)
        
        # Get all tables
        tables = inspector.get_all_tables()
        print(f"\n📋 Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Save detailed analysis
        print("\n📊 Analyzing schema...")
        schema_dict = inspector.save_schema_analysis("database_schema_analysis.json")
        print("✅ Schema analysis saved to database_schema_analysis.json")
        
        # Generate models
        print("\n🔨 Generating SQLAlchemy models...")
        models_code = inspector.generate_all_models()
        
        # Save to file
        output_file = "api/models_generated.py"
        with open(output_file, 'w') as f:
            f.write(models_code)
        
        print(f"✅ Models generated and saved to {output_file}")
        
        # Show summary
        print("\n📈 Summary:")
        for table_name, info in schema_dict.items():
            print(f"\n  {table_name}:")
            print(f"    - Columns: {len(info['columns'])}")
            print(f"    - Relationships: {len(info['relationships'])}")
            if info['relationships']:
                for rel in info['relationships']:
                    print(f"      → {rel['referenced_table']}")
        
        print("\n✨ Done! Next steps:")
        print("1. Review the generated models in api/models_generated.py")
        print("2. Replace api/models.py with the generated version")
        print("3. Update api/schemas.py to match the new models")
        print("4. Test all endpoints")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 If psycopg2 is not installed, you can:")
        print("1. Run: pip install psycopg2-binary")
        print("2. Or use the /inspect-schema endpoint once deployed")

if __name__ == "__main__":
    main()