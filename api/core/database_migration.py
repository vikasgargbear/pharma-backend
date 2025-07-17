"""
Database Migration System
Handles schema synchronization between models and database
"""

from typing import Dict, List, Optional, Any
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseMigrationManager:
    """Manages database schema migrations and model synchronization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inspector = inspect(db.bind)
        
    def get_database_schema(self) -> Dict[str, Any]:
        """Get current database schema"""
        schema = {}
        
        try:
            # Get all tables
            tables = self.inspector.get_table_names()
            
            for table in tables:
                columns = self.inspector.get_columns(table)
                primary_keys = self.inspector.get_pk_constraint(table)
                foreign_keys = self.inspector.get_foreign_keys(table)
                indexes = self.inspector.get_indexes(table)
                
                schema[table] = {
                    'columns': columns,
                    'primary_keys': primary_keys,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes
                }
                
            return schema
            
        except Exception as e:
            logger.error(f"Error getting database schema: {e}")
            raise
    
    def compare_with_models(self, models: Dict[str, Any]) -> Dict[str, List[str]]:
        """Compare database schema with SQLAlchemy models"""
        db_schema = self.get_database_schema()
        differences = {
            'missing_tables': [],
            'extra_tables': [],
            'column_mismatches': {},
            'type_mismatches': {}
        }
        
        # Check for missing/extra tables
        db_tables = set(db_schema.keys())
        model_tables = set(models.keys())
        
        differences['missing_tables'] = list(model_tables - db_tables)
        differences['extra_tables'] = list(db_tables - model_tables)
        
        # Check column differences for common tables
        for table in db_tables.intersection(model_tables):
            db_columns = {col['name']: col for col in db_schema[table]['columns']}
            model_columns = {col['name']: col for col in models[table]['columns']}
            
            # Missing columns in database
            missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
            # Extra columns in database
            extra_in_db = set(db_columns.keys()) - set(model_columns.keys())
            
            if missing_in_db or extra_in_db:
                differences['column_mismatches'][table] = {
                    'missing_in_db': list(missing_in_db),
                    'extra_in_db': list(extra_in_db)
                }
            
            # Check type mismatches
            for col_name in set(db_columns.keys()).intersection(set(model_columns.keys())):
                db_type = str(db_columns[col_name]['type'])
                model_type = str(model_columns[col_name]['type'])
                
                # Normalize types for comparison
                if not self._types_compatible(db_type, model_type):
                    if table not in differences['type_mismatches']:
                        differences['type_mismatches'][table] = {}
                    differences['type_mismatches'][table][col_name] = {
                        'database': db_type,
                        'model': model_type
                    }
        
        return differences
    
    def _types_compatible(self, db_type: str, model_type: str) -> bool:
        """Check if database type and model type are compatible"""
        # Normalize types
        db_type = db_type.upper()
        model_type = model_type.upper()
        
        # Direct match
        if db_type == model_type:
            return True
        
        # Common equivalences
        equivalences = [
            ('VARCHAR', 'STRING'),
            ('TEXT', 'STRING'),
            ('TIMESTAMP', 'DATETIME'),
            ('DECIMAL', 'NUMERIC'),
            ('SERIAL', 'INTEGER'),
            ('BIGSERIAL', 'BIGINT')
        ]
        
        for equiv in equivalences:
            if (db_type in equiv and model_type in equiv) or \
               (any(t in db_type for t in equiv) and any(t in model_type for t in equiv)):
                return True
        
        return False
    
    def generate_migration_sql(self, differences: Dict[str, Any]) -> List[str]:
        """Generate SQL statements to fix differences"""
        sql_statements = []
        
        # Create missing tables
        for table in differences.get('missing_tables', []):
            # This would require model metadata
            sql_statements.append(f"-- TODO: CREATE TABLE {table}")
        
        # Handle column mismatches
        for table, mismatches in differences.get('column_mismatches', {}).items():
            for col in mismatches.get('missing_in_db', []):
                sql_statements.append(f"-- TODO: ALTER TABLE {table} ADD COLUMN {col}")
            
            for col in mismatches.get('extra_in_db', []):
                sql_statements.append(f"-- WARNING: Extra column in database: {table}.{col}")
        
        # Handle type mismatches
        for table, columns in differences.get('type_mismatches', {}).items():
            for col, types in columns.items():
                sql_statements.append(
                    f"-- WARNING: Type mismatch in {table}.{col}: "
                    f"DB has {types['database']}, Model expects {types['model']}"
                )
        
        return sql_statements
    
    def create_migration_record(self, name: str, description: str) -> int:
        """Create a migration record"""
        try:
            result = self.db.execute(text("""
                INSERT INTO schema_migrations (name, description, applied_at)
                VALUES (:name, :description, :applied_at)
                RETURNING id
            """), {
                'name': name,
                'description': description,
                'applied_at': datetime.utcnow()
            })
            self.db.commit()
            return result.fetchone()[0]
        except SQLAlchemyError:
            # Table might not exist
            self._create_migration_table()
            return self.create_migration_record(name, description)
    
    def _create_migration_table(self):
        """Create schema_migrations table if it doesn't exist"""
        self.db.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                applied_at TIMESTAMP NOT NULL,
                rollback_sql TEXT,
                status VARCHAR(50) DEFAULT 'applied'
            )
        """))
        self.db.commit()
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations"""
        try:
            result = self.db.execute(text("""
                SELECT id, name, description, applied_at, status
                FROM schema_migrations
                ORDER BY applied_at DESC
            """))
            return [dict(row) for row in result]
        except SQLAlchemyError:
            return []
    
    def auto_fix_simple_issues(self) -> Dict[str, Any]:
        """Automatically fix simple schema issues"""
        fixes_applied = {
            'renamed_columns': [],
            'added_defaults': [],
            'fixed_nullability': []
        }
        
        # Common column renames in pharma databases
        column_renames = [
            ('batches', 'mfg_date', 'manufacturing_date'),
            ('batches', 'manufacture_date', 'manufacturing_date'),
            ('products', 'model_number', 'product_code'),
            ('customers', 'contact_person', 'contact_name')
        ]
        
        for table, old_col, new_col in column_renames:
            if self._column_exists(table, old_col) and not self._column_exists(table, new_col):
                try:
                    self.db.execute(text(f"""
                        ALTER TABLE {table} 
                        RENAME COLUMN {old_col} TO {new_col}
                    """))
                    self.db.commit()
                    fixes_applied['renamed_columns'].append(f"{table}.{old_col} → {new_col}")
                except SQLAlchemyError as e:
                    logger.error(f"Failed to rename column: {e}")
                    self.db.rollback()
        
        return fixes_applied
    
    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table"""
        try:
            columns = self.inspector.get_columns(table)
            return any(col['name'] == column for col in columns)
        except:
            return False

class SchemaReconciler:
    """Reconciles differences between models and database"""
    
    @staticmethod
    def generate_minimal_models(schema: Dict[str, Any]) -> str:
        """Generate minimal SQLAlchemy models that match the database exactly"""
        models_code = '''"""
Minimal SQLAlchemy models that match the actual database schema
Auto-generated to ensure compatibility
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

'''
        
        # Generate each model
        for table_name, table_info in schema.items():
            class_name = ''.join(word.capitalize() for word in table_name.split('_'))
            
            models_code += f"class {class_name}(Base):\n"
            models_code += f'    __tablename__ = "{table_name}"\n\n'
            
            # Add columns
            for col in table_info['columns']:
                col_name = col['name']
                col_type = str(col['type'])
                
                # Map database types to SQLAlchemy
                if 'INT' in col_type.upper():
                    sa_type = 'Integer'
                elif 'VARCHAR' in col_type.upper() or 'TEXT' in col_type.upper():
                    sa_type = 'String' if 'VARCHAR' in col_type.upper() else 'Text'
                elif 'NUMERIC' in col_type.upper() or 'DECIMAL' in col_type.upper():
                    sa_type = 'Numeric(10, 2)'
                elif 'DATE' in col_type.upper():
                    sa_type = 'DateTime' if 'TIME' in col_type.upper() else 'Date'
                elif 'BOOL' in col_type.upper():
                    sa_type = 'Boolean'
                else:
                    sa_type = 'String'  # Default
                
                # Check if primary key
                is_pk = False
                if table_info.get('primary_keys'):
                    is_pk = col_name in table_info['primary_keys'].get('constrained_columns', [])
                
                # Build column definition
                col_def = f"    {col_name} = Column({sa_type}"
                
                if is_pk:
                    col_def += ", primary_key=True"
                    if 'serial' in col_type.lower():
                        col_def += ", autoincrement=True"
                
                # Add foreign keys
                for fk in table_info.get('foreign_keys', []):
                    if col_name in fk.get('constrained_columns', []):
                        ref_table = fk['referred_table']
                        ref_col = fk['referred_columns'][0]
                        col_def += f', ForeignKey("{ref_table}.{ref_col}")'
                
                if not col['nullable'] and not is_pk:
                    col_def += ", nullable=False"
                
                # Handle defaults
                if col.get('default'):
                    if 'now()' in str(col['default']):
                        col_def += ", default=datetime.utcnow"
                
                col_def += ")\n"
                models_code += col_def
            
            models_code += "\n"
        
        return models_code