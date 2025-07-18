"""
Simple Database Inspection Router
Minimal implementation to avoid import issues
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db

router = APIRouter(prefix="/db-inspect", tags=["database-inspection"])

@router.get("/tables")
async def get_tables(db: Session = Depends(get_db)):
    """Get list of all tables in the database"""
    try:
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result]
        return {"tables": tables, "count": len(tables)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")

@router.get("/table/{table_name}/columns")
async def get_table_columns(table_name: str, db: Session = Depends(get_db)):
    """Get columns for a specific table"""
    try:
        result = db.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get columns: {str(e)}")

@router.get("/full-schema")
async def get_full_schema(db: Session = Depends(get_db)):
    """Get complete database schema"""
    try:
        # Get all tables
        tables_result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        schema = {}
        
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
            
            schema[table_name] = []
            for col in columns_result:
                schema[table_name].append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == 'YES',
                    "default": col[3]
                })
        
        return {"database_schema": schema}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema inspection failed: {str(e)}")

@router.post("/fix-column/{table_name}")
async def fix_column_name(
    table_name: str,
    old_name: str,
    new_name: str,
    db: Session = Depends(get_db)
):
    """Rename a column in a table"""
    try:
        # Check if old column exists
        check_result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :old_name
            AND table_schema = 'public'
        """), {"table_name": table_name, "old_name": old_name})
        
        if not check_result.fetchone():
            return {"status": "error", "message": f"Column {old_name} not found in {table_name}"}
        
        # Rename the column
        db.execute(text(f"""
            ALTER TABLE {table_name} 
            RENAME COLUMN {old_name} TO {new_name}
        """))
        db.commit()
        
        return {
            "status": "success",
            "message": f"Renamed {table_name}.{old_name} to {table_name}.{new_name}"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to rename column: {str(e)}")

@router.get("/query")
async def execute_query(sql: str, db: Session = Depends(get_db)):
    """Execute a simple SELECT query (read-only)"""
    try:
        if not sql.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries allowed")
            
        result = db.execute(text(sql))
        rows = []
        for row in result:
            rows.append(dict(row._mapping))
        
        return {"result": rows, "count": len(rows)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")