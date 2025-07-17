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
from ..migrations.add_order_columns import (
    add_order_enterprise_columns,
    create_sample_order_data
)
from ..migrations.fix_order_columns import fix_missing_columns
from ..migrations.add_inventory_tables import (
    add_inventory_enterprise_tables,
    get_existing_tables
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


@router.post("/add-order-columns")
async def run_order_migration(db: Session = Depends(get_db)):
    """Add all missing columns for enterprise order management"""
    try:
        logger.info("Starting order column migration...")
        result = add_order_enterprise_columns(db)
        
        if result["success"]:
            logger.info(f"Order migration successful: {result['message']}")
        else:
            logger.error(f"Order migration failed: {result['message']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Order migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fix-order-columns")
async def fix_order_columns(db: Session = Depends(get_db)):
    """Quick fix for missing order columns"""
    try:
        result = fix_missing_columns(db)
        return result
    except Exception as e:
        logger.error(f"Fix columns error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-sample-orders")
async def create_sample_orders(db: Session = Depends(get_db)):
    """Create sample order data for testing"""
    try:
        logger.info("Creating sample order data...")
        result = create_sample_order_data(db)
        
        if result["success"]:
            logger.info(f"Sample orders created: {result['message']}")
        else:
            logger.error(f"Sample orders failed: {result['message']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Sample order error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-inventory-tables")
async def run_inventory_migration(db: Session = Depends(get_db)):
    """Add inventory tables for batch tracking and stock movements"""
    try:
        logger.info("Starting inventory tables migration...")
        result = add_inventory_enterprise_tables(db)
        
        if result["success"]:
            logger.info(f"Inventory migration successful: {result['message']}")
        else:
            logger.error(f"Inventory migration failed: {result['message']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Inventory migration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-inventory-tables")
async def check_inventory_tables(db: Session = Depends(get_db)):
    """Check if inventory tables exist"""
    try:
        tables = get_existing_tables(db)
        
        required_tables = ["batches", "inventory_movements"]
        existing = [t for t in required_tables if t in tables]
        missing = [t for t in required_tables if t not in tables]
        
        # Check batch count
        batch_count = 0
        movement_count = 0
        
        if "batches" in tables:
            batch_count = db.execute(text("SELECT COUNT(*) FROM batches")).scalar()
        
        if "inventory_movements" in tables:
            movement_count = db.execute(text("SELECT COUNT(*) FROM inventory_movements")).scalar()
        
        return {
            "inventory_ready": len(missing) == 0,
            "existing_tables": existing,
            "missing_tables": missing,
            "batch_count": batch_count,
            "movement_count": movement_count
        }
        
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/migration-plan")
async def get_migration_plan():
    """Get the migration plan for scaling the database"""
    return {
        "description": "Enterprise Pharma System Migration Plan",
        "customer_migration": {
            "completed": True,
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
            ]
        },
        "order_migration": {
            "completed": True,
            "steps": [
                {
                    "step": 1,
                    "action": "Add order columns",
                    "endpoint": "POST /migrations/v2/add-order-columns",
                    "safe": True,
                    "note": "Adds order management columns"
                },
                {
                    "step": 2,
                    "action": "Create sample orders",
                    "endpoint": "POST /migrations/v2/create-sample-orders",
                    "safe": True,
                    "note": "Creates orders with products"
                },
                {
                    "step": 3,
                    "action": "Test order endpoints",
                    "endpoint": "GET /api/v1/orders/",
                    "safe": True
                }
            ]
        },
        "inventory_migration": {
            "steps": [
                {
                    "step": 1,
                    "action": "Check existing inventory tables",
                    "endpoint": "GET /migrations/v2/check-inventory-tables",
                    "safe": True
                },
                {
                    "step": 2,
                    "action": "Add inventory tables",
                    "endpoint": "POST /migrations/v2/add-inventory-tables",
                    "safe": True,
                    "note": "Creates batches and inventory_movements tables"
                },
                {
                    "step": 3,
                    "action": "Test inventory endpoints",
                    "endpoint": "GET /api/v1/inventory/stock/current",
                    "safe": True
                }
            ]
        },
        "benefits": [
            "GST compliance with GSTIN validation",
            "Credit limit management",
            "Multi-type customers (retail, wholesale, hospital, pharmacy)",
            "Contact tracking with phone and email",
            "Address management for delivery",
            "Discount and payment terms"
        ]
    }