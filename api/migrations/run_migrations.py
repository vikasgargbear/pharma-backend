"""
Automatic migration runner for production deployments
Runs all necessary database migrations on startup
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

def run_all_migrations():
    """Run all pending migrations in order"""
    migrations_run = []
    migrations_failed = []
    
    # DISABLED: Using new enterprise database schema from production-infra
    print("⚠️  Migrations disabled - using new enterprise database schema")
    print("   All schema changes should be made in production-infra/database")
    return
    
    print("🔄 Starting database migrations...")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print("-" * 50)
    
    # List of migrations to run in order
    migrations = [
        # Add pack fields migration (highest priority)
        {
            "name": "add_pack_fields",
            "description": "Add pack configuration fields to products table",
            "module": "api.migrations.add_pack_fields"
        },
        # Add more migrations here as needed
    ]
    
    for migration in migrations:
        try:
            print(f"\n🔧 Running migration: {migration['name']}")
            print(f"   Description: {migration['description']}")
            
            # Import and run the migration
            module = __import__(migration['module'], fromlist=['run_migration'])
            if hasattr(module, 'run_migration'):
                success = module.run_migration()
                if success:
                    migrations_run.append(migration['name'])
                    print(f"   ✅ Success: {migration['name']}")
                else:
                    migrations_failed.append(migration['name'])
                    print(f"   ❌ Failed: {migration['name']}")
            else:
                print(f"   ⚠️  Skipped: No run_migration function found")
                
        except Exception as e:
            migrations_failed.append(migration['name'])
            print(f"   ❌ Error running {migration['name']}: {e}")
            logger.error(f"Migration {migration['name']} failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Migration Summary:")
    print(f"   ✅ Successful: {len(migrations_run)} migrations")
    if migrations_run:
        for m in migrations_run:
            print(f"      - {m}")
    print(f"   ❌ Failed: {len(migrations_failed)} migrations")
    if migrations_failed:
        for m in migrations_failed:
            print(f"      - {m}")
    print("=" * 50 + "\n")
    
    # Return True if all migrations succeeded
    return len(migrations_failed) == 0

if __name__ == "__main__":
    # Run migrations
    success = run_all_migrations()
    
    if success:
        print("✅ All migrations completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some migrations failed. Check logs for details.")
        sys.exit(1)