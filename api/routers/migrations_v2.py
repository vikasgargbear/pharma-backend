"""
Database migration endpoints for adding enterprise features
This is how companies scale - controlled migrations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db
from ..migrations.add_customer_columns import (
    add_customer_enterprise_columns,
    create_sample_customer_data,
    get_existing_columns
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migrations/v2", tags=["migrations-v2"])


@router.get("/check-customer-columns")
async def check_customer_columns(db: Session = Depends(get_db)):
    """Check which columns exist in customers table"""
    try:
        columns = get_existing_columns(db, "customers")
        
        # Define what we expect
        expected_columns = [
            "customer_id", "customer_name", "customer_code", "contact_person",
            "phone", "email", "address_line1", "city", "state", "pincode",
            "gstin", "customer_type", "credit_limit", "credit_days",
            "is_active", "org_id", "created_at", "updated_at"
        ]
        
        missing = [col for col in expected_columns if col not in columns]
        extra = [col for col in columns if col not in expected_columns]
        
        return {
            "existing_columns": columns,
            "expected_columns": expected_columns,
            "missing_columns": missing,
            "extra_columns": extra,
            "ready_for_enterprise": len(missing) == 0
        }
        
    except Exception as e:
        logger.error(f"Error checking columns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-customer-columns")
async def run_customer_migration(db: Session = Depends(get_db)):
    """Add all missing columns for enterprise customer management"""
    try:
        logger.info("Starting customer column migration...")
        result = add_customer_enterprise_columns(db)
        
        if result["success"]:
            logger.info(f"Migration successful: {result['message']}")
        else:
            logger.error(f"Migration failed: {result['message']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-sample-customers")
async def create_sample_customers(db: Session = Depends(get_db)):
    """Create sample customer data for testing"""
    try:
        logger.info("Creating sample customer data...")
        result = create_sample_customer_data(db)
        
        if result["success"]:
            logger.info(f"Sample data created: {result['message']}")
        else:
            logger.error(f"Sample data failed: {result['message']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Sample data error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration-plan")
async def get_migration_plan():
    """Get the migration plan for scaling the database"""
    return {
        "description": "Enterprise Customer Management Migration Plan",
        "steps": [
            {
                "step": 1,
                "action": "Check existing columns",
                "endpoint": "GET /migrations/v2/check-customer-columns",
                "safe": True
            },
            {
                "step": 2,
                "action": "Add missing columns",
                "endpoint": "POST /migrations/v2/add-customer-columns",
                "safe": True,
                "note": "Adds columns without affecting existing data"
            },
            {
                "step": 3,
                "action": "Create sample data",
                "endpoint": "POST /migrations/v2/create-sample-customers",
                "safe": True,
                "note": "Only creates data if table is empty"
            },
            {
                "step": 4,
                "action": "Test customer endpoints",
                "endpoint": "GET /api/v1/customers/",
                "safe": True
            }
        ],
        "benefits": [
            "GST compliance with GSTIN validation",
            "Credit limit management",
            "Multi-type customers (retail, wholesale, hospital, pharmacy)",
            "Contact tracking with phone and email",
            "Address management for delivery",
            "Discount and payment terms"
        ]
    }