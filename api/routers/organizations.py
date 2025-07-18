"""
Organizations management router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

from ..database import get_db

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/create-default")
async def create_default_organization(db: Session = Depends(get_db)):
    """Create a default organization for testing"""
    try:
        # Check if organizations table exists
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'organizations'
        """))
        
        if result.scalar() == 0:
            return {
                "error": "Organizations table does not exist",
                "default_org_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        
        # Check if any organization exists
        existing = db.execute(text("SELECT org_id, org_name FROM organizations LIMIT 1"))
        row = existing.fetchone()
        
        if row:
            return {
                "message": "Organization already exists",
                "org_id": str(row[0]),
                "org_name": row[1]
            }
        
        # Create new organization
        new_org_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO organizations (org_id, org_name, business_type, is_active)
            VALUES (:org_id, 'Default Pharma', 'pharmacy', true)
        """), {"org_id": new_org_id})
        
        db.commit()
        
        return {
            "message": "Default organization created",
            "org_id": new_org_id,
            "org_name": "Default Pharma"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

@router.get("/list")
async def list_organizations(db: Session = Depends(get_db)):
    """List all organizations"""
    try:
        result = db.execute(text("""
            SELECT org_id, org_name, business_type, is_active 
            FROM organizations 
            ORDER BY created_at DESC
        """))
        
        orgs = []
        for row in result:
            orgs.append({
                "org_id": str(row[0]),
                "org_name": row[1],
                "business_type": row[2],
                "is_active": row[3]
            })
        
        return {"organizations": orgs, "count": len(orgs)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list organizations: {str(e)}")