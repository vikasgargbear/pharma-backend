"""
Quick fix to create a default organization and update schemas
"""
import uuid
from sqlalchemy import text
from api.database import engine

def create_default_org():
    """Create a default organization for testing"""
    org_id = str(uuid.uuid4())
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Check if organizations table exists
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'organizations'
            """))
            
            if result.scalar() > 0:
                # Check if any org exists
                existing = conn.execute(text("SELECT org_id FROM organizations LIMIT 1"))
                row = existing.fetchone()
                
                if row:
                    trans.rollback()
                    return row[0]
                
                # Create default org
                conn.execute(text("""
                    INSERT INTO organizations (org_id, org_name, org_code, is_active)
                    VALUES (:org_id, 'Default Organization', 'DEFAULT', true)
                """), {"org_id": org_id})
                
                trans.commit()
                print(f"Created default organization: {org_id}")
                return org_id
            else:
                trans.rollback()
                print("Organizations table not found, using fixed UUID")
                return "550e8400-e29b-41d4-a716-446655440000"
                
        except Exception as e:
            trans.rollback()
            print(f"Error creating organization: {e}")
            return "550e8400-e29b-41d4-a716-446655440000"

if __name__ == "__main__":
    org_id = create_default_org()
    print(f"Default org_id to use: {org_id}")