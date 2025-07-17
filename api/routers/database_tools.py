"""
Database Tools Router
Sophisticated database schema management and debugging tools
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import Dict, Any, List
import json

from ..database import get_db
from ..core.database_migration import DatabaseMigrationManager, SchemaReconciler

router = APIRouter(prefix="/database-tools", tags=["database-tools"])

@router.get("/schema/inspect")
async def inspect_database_schema(db: Session = Depends(get_db)):
    """Inspect complete database schema with all details"""
    try:
        migration_manager = DatabaseMigrationManager(db)
        schema = migration_manager.get_database_schema()
        
        # Enhance with statistics
        stats = {
            'total_tables': len(schema),
            'total_columns': sum(len(table['columns']) for table in schema.values()),
            'tables_with_fk': sum(1 for table in schema.values() if table.get('foreign_keys')),
            'indexed_tables': sum(1 for table in schema.values() if table.get('indexes'))
        }
        
        return {
            'schema': schema,
            'statistics': stats,
            'database_type': 'PostgreSQL'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema inspection failed: {str(e)}")

@router.get("/schema/tables")
async def list_tables(db: Session = Depends(get_db)):
    """List all tables with basic info"""
    try:
        result = db.execute(text("""
            SELECT 
                t.table_name,
                COUNT(c.column_name) as column_count,
                pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name)::regclass)) as table_size,
                obj_description(quote_ident(t.table_name)::regclass) as description
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name
            ORDER BY t.table_name
        """))
        
        tables = []
        for row in result:
            tables.append({
                'name': row[0],
                'column_count': row[1],
                'size': row[2] if row[2] else 'Unknown',
                'description': row[3]
            })
        
        return {'tables': tables, 'count': len(tables)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@router.get("/schema/table/{table_name}")
async def get_table_details(table_name: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific table"""
    try:
        # Get columns
        columns_result = db.execute(text("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        
        columns = []
        for col in columns_result:
            columns.append({
                'name': col[0],
                'type': col[1],
                'max_length': col[2],
                'nullable': col[3] == 'YES',
                'default': col[4],
                'position': col[5]
            })
        
        # Get primary keys
        pk_result = db.execute(text("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = :table_name::regclass
            AND i.indisprimary
        """), {"table_name": table_name})
        
        primary_keys = [row[0] for row in pk_result]
        
        # Get foreign keys
        fk_result = db.execute(text("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = :table_name
        """), {"table_name": table_name})
        
        foreign_keys = []
        for fk in fk_result:
            foreign_keys.append({
                'column': fk[0],
                'references': f"{fk[1]}.{fk[2]}"
            })
        
        # Get row count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = count_result.scalar()
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'row_count': row_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table details: {str(e)}")

@router.post("/schema/auto-fix")
async def auto_fix_schema_issues(db: Session = Depends(get_db)):
    """Automatically fix common schema issues"""
    try:
        migration_manager = DatabaseMigrationManager(db)
        fixes = migration_manager.auto_fix_simple_issues()
        
        # Create migration record
        if any(fixes.values()):
            migration_manager.create_migration_record(
                "auto_fix_schema",
                f"Automatically fixed schema issues: {json.dumps(fixes)}"
            )
        
        return {
            'status': 'success',
            'fixes_applied': fixes,
            'message': 'Schema issues have been automatically fixed where possible'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-fix failed: {str(e)}")

@router.get("/schema/generate-models")
async def generate_models_from_schema(db: Session = Depends(get_db)):
    """Generate SQLAlchemy models that match the current database"""
    try:
        migration_manager = DatabaseMigrationManager(db)
        schema = migration_manager.get_database_schema()
        
        models_code = SchemaReconciler.generate_minimal_models(schema)
        
        return {
            'status': 'success',
            'models_code': models_code,
            'instructions': [
                '1. Save the models_code to a new file (e.g., models_minimal.py)',
                '2. Test with a few endpoints to ensure compatibility',
                '3. Gradually migrate from the old models to the new ones',
                '4. Add additional fields and relationships as needed'
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model generation failed: {str(e)}")

@router.get("/schema/test-query/{table_name}")
async def test_table_query(table_name: str, limit: int = 5, db: Session = Depends(get_db)):
    """Test querying a table to verify schema compatibility"""
    try:
        # Validate table exists
        tables_result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name = :table_name
        """), {"table_name": table_name})
        
        if not tables_result.fetchone():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Get sample data
        result = db.execute(text(f"SELECT * FROM {table_name} LIMIT :limit"), {"limit": limit})
        
        # Get column names
        columns = result.keys()
        
        # Convert rows to dictionaries
        rows = []
        for row in result:
            rows.append(dict(zip(columns, row)))
        
        return {
            'table': table_name,
            'columns': list(columns),
            'row_count': len(rows),
            'sample_data': rows
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("/migrations/history")
async def get_migration_history(db: Session = Depends(get_db)):
    """Get history of all applied migrations"""
    try:
        migration_manager = DatabaseMigrationManager(db)
        migrations = migration_manager.get_applied_migrations()
        
        return {
            'migrations': migrations,
            'total': len(migrations)
        }
        
    except Exception as e:
        return {
            'migrations': [],
            'total': 0,
            'note': 'Migration tracking not yet initialized'
        }