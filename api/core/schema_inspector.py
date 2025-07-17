"""
Database Schema Inspector
Sophisticated tool to analyze and generate models from existing database
"""

from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.engine import Engine
from dataclasses import dataclass
import json

@dataclass
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    primary_key: bool
    foreign_key: Optional[str] = None
    default: Optional[str] = None
    
@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo]
    relationships: List[Dict[str, str]]
    indexes: List[str]
    
class DatabaseSchemaInspector:
    """Sophisticated database schema inspector"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url.replace("postgresql://", "postgresql+psycopg2://"))
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        
    def get_all_tables(self) -> List[str]:
        """Get all table names in the database"""
        return self.inspector.get_table_names()
    
    def inspect_table(self, table_name: str) -> TableInfo:
        """Get detailed information about a table"""
        columns = []
        
        # Get column information
        for col in self.inspector.get_columns(table_name):
            column_info = ColumnInfo(
                name=col['name'],
                type=str(col['type']),
                nullable=col['nullable'],
                primary_key=False,
                default=col.get('default')
            )
            columns.append(column_info)
        
        # Get primary keys
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        if pk_constraint:
            for col in pk_constraint['constrained_columns']:
                for column in columns:
                    if column.name == col:
                        column.primary_key = True
        
        # Get foreign keys
        fk_constraints = self.inspector.get_foreign_keys(table_name)
        for fk in fk_constraints:
            for col in fk['constrained_columns']:
                for column in columns:
                    if column.name == col:
                        column.foreign_key = f"{fk['referred_table']}.{fk['referred_columns'][0]}"
        
        # Get relationships
        relationships = []
        for fk in fk_constraints:
            relationships.append({
                'column': fk['constrained_columns'][0],
                'referenced_table': fk['referred_table'],
                'referenced_column': fk['referred_columns'][0]
            })
        
        # Get indexes
        indexes = [idx['name'] for idx in self.inspector.get_indexes(table_name)]
        
        return TableInfo(
            name=table_name,
            columns=columns,
            relationships=relationships,
            indexes=indexes
        )
    
    def inspect_full_schema(self) -> Dict[str, TableInfo]:
        """Inspect the entire database schema"""
        schema = {}
        for table_name in self.get_all_tables():
            schema[table_name] = self.inspect_table(table_name)
        return schema
    
    def generate_sqlalchemy_model(self, table_info: TableInfo) -> str:
        """Generate SQLAlchemy model code from table info"""
        # Convert table name to class name (snake_case to PascalCase)
        class_name = ''.join(word.capitalize() for word in table_info.name.split('_'))
        
        model_code = f"class {class_name}(Base):\n"
        model_code += f'    __tablename__ = "{table_info.name}"\n\n'
        
        # Add columns
        for col in table_info.columns:
            col_def = f"    {col.name} = Column("
            
            # Map SQL types to SQLAlchemy types
            type_mapping = {
                'INTEGER': 'Integer',
                'BIGINT': 'BigInteger',
                'SMALLINT': 'SmallInteger',
                'NUMERIC': 'Numeric',
                'DECIMAL': 'Numeric',
                'FLOAT': 'Float',
                'REAL': 'Float',
                'DOUBLE PRECISION': 'Float',
                'VARCHAR': 'String',
                'CHAR': 'String',
                'TEXT': 'Text',
                'DATE': 'Date',
                'TIMESTAMP': 'DateTime',
                'TIMESTAMP WITHOUT TIME ZONE': 'DateTime',
                'TIMESTAMP WITH TIME ZONE': 'DateTime',
                'BOOLEAN': 'Boolean',
                'UUID': 'String',
                'JSON': 'JSON',
                'JSONB': 'JSON'
            }
            
            # Get base type
            sql_type = col.type.upper()
            sqlalchemy_type = 'String'  # Default
            
            for sql_t, sa_t in type_mapping.items():
                if sql_t in sql_type:
                    sqlalchemy_type = sa_t
                    break
            
            # Handle string length
            if 'VARCHAR' in sql_type and '(' in col.type:
                length = col.type.split('(')[1].split(')')[0]
                col_def += f"{sqlalchemy_type}({length})"
            elif 'NUMERIC' in sql_type and '(' in col.type:
                precision = col.type.split('(')[1].split(')')[0]
                col_def += f"{sqlalchemy_type}({precision})"
            else:
                col_def += sqlalchemy_type
            
            # Add constraints
            if col.primary_key:
                col_def += ", primary_key=True"
                if 'serial' in col.type.lower() or 'identity' in col.type.lower():
                    col_def += ", autoincrement=True"
            
            if col.foreign_key:
                col_def += f', ForeignKey("{col.foreign_key}")'
            
            if not col.nullable and not col.primary_key:
                col_def += ", nullable=False"
            
            if col.default:
                if 'now()' in str(col.default) or 'CURRENT_TIMESTAMP' in str(col.default):
                    col_def += ", default=datetime.utcnow"
                elif col.default != 'NULL':
                    col_def += f", default={col.default}"
            
            col_def += ")\n"
            model_code += col_def
        
        # Add relationships
        if table_info.relationships:
            model_code += "\n    # Relationships\n"
            for rel in table_info.relationships:
                related_class = ''.join(word.capitalize() for word in rel['referenced_table'].split('_'))
                rel_name = rel['referenced_table'].rstrip('s')  # Simple pluralization
                model_code += f'    # {rel_name} = relationship("{related_class}", back_populates="{table_info.name}")\n'
        
        return model_code
    
    def generate_all_models(self) -> str:
        """Generate all SQLAlchemy models for the database"""
        schema = self.inspect_full_schema()
        
        models_code = '''"""
Auto-generated SQLAlchemy models from existing database
Generated by DatabaseSchemaInspector
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text, Numeric, Boolean, BigInteger, SmallInteger, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

'''
        
        # Sort tables to handle dependencies
        sorted_tables = self._sort_tables_by_dependencies(schema)
        
        for table_name in sorted_tables:
            table_info = schema[table_name]
            models_code += self.generate_sqlalchemy_model(table_info)
            models_code += "\n\n"
        
        return models_code
    
    def _sort_tables_by_dependencies(self, schema: Dict[str, TableInfo]) -> List[str]:
        """Sort tables by foreign key dependencies"""
        # Build dependency graph
        dependencies = {}
        for table_name, table_info in schema.items():
            deps = set()
            for rel in table_info.relationships:
                if rel['referenced_table'] != table_name:  # Avoid self-references
                    deps.add(rel['referenced_table'])
            dependencies[table_name] = deps
        
        # Topological sort
        sorted_tables = []
        visited = set()
        
        def visit(table):
            if table in visited:
                return
            visited.add(table)
            for dep in dependencies.get(table, []):
                if dep in schema:  # Only process existing tables
                    visit(dep)
            sorted_tables.append(table)
        
        for table in schema:
            visit(table)
        
        return sorted_tables
    
    def save_schema_analysis(self, filename: str = "schema_analysis.json"):
        """Save detailed schema analysis to JSON file"""
        schema = self.inspect_full_schema()
        
        # Convert to serializable format
        schema_dict = {}
        for table_name, table_info in schema.items():
            schema_dict[table_name] = {
                'columns': [
                    {
                        'name': col.name,
                        'type': col.type,
                        'nullable': col.nullable,
                        'primary_key': col.primary_key,
                        'foreign_key': col.foreign_key,
                        'default': str(col.default) if col.default else None
                    }
                    for col in table_info.columns
                ],
                'relationships': table_info.relationships,
                'indexes': table_info.indexes
            }
        
        with open(filename, 'w') as f:
            json.dump(schema_dict, f, indent=2)
        
        return schema_dict