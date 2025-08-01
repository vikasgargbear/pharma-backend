"""
Debug endpoint to get organization info
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...database import get_db

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])


@router.get("/organizations")
async def get_organizations(db: Session = Depends(get_db)):
    """Get all organizations for debugging"""
    try:
        result = db.execute(text("""
            SELECT org_id, org_code, org_name 
            FROM master.organizations 
            WHERE is_active = true
            LIMIT 10
        """))
        
        orgs = []
        for row in result:
            orgs.append({
                "org_id": str(row.org_id),
                "org_code": row.org_code,
                "org_name": row.org_name
            })
        
        return {"organizations": orgs}
    except Exception as e:
        return {"error": str(e), "message": "No organizations found or table doesn't exist"}