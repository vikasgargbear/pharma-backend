#!/usr/bin/env python3
"""
Test minimal API to understand what database schema exists
"""

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import Session, sessionmaker
import os

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.zsqnogqhvkbgkpqcvqdb:AASOdatabase123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres')

# Create engine
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Schema Inspector")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Schema Inspector API"}

@app.get("/tables")
def get_tables(db: Session = Depends(get_db)):
    """Get all table names"""
    result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """))
    
    tables = [row[0] for row in result]
    return {"tables": tables}

@app.get("/table/{table_name}")
def get_table_schema(table_name: str, db: Session = Depends(get_db)):
    """Get schema for a specific table"""
    result = db.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = :table_name 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """), {"table_name": table_name})
    
    columns = []
    for row in result:
        columns.append({
            "name": row[0],
            "type": row[1],
            "nullable": row[2] == 'YES',
            "default": row[3]
        })
    
    return {"table": table_name, "columns": columns}

@app.get("/full-schema")
def get_full_schema(db: Session = Depends(get_db)):
    """Get complete database schema"""
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
    
    return schema_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)