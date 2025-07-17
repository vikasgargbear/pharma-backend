"""
Run database migration on Railway deployment
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.migrations.make_org_id_nullable import run_migration

if __name__ == "__main__":
    print("Running migration to make org_id nullable...")
    run_migration()