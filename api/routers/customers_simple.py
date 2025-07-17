"""
Simplified customer endpoints that work with existing database schema
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
import logging

from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers-simple", tags=["customers-simple"])

# Default organization ID
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


@router.get("/")
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List customers from the database"""
    try:
        query = "SELECT * FROM customers WHERE 1=1"
        params = {"limit": limit, "skip": skip}
        
        if search:
            query += " AND customer_name ILIKE :search"
            params["search"] = f"%{search}%"
        
        query += " ORDER BY customer_id DESC LIMIT :limit OFFSET :skip"
        
        result = db.execute(text(query), params)
        customers = []
        
        for row in result:
            customer_dict = dict(row._mapping)
            customers.append(customer_dict)
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM customers"
        if search:
            count_query += " WHERE customer_name ILIKE :search"
            total = db.execute(text(count_query), {"search": f"%{search}%"}).scalar()
        else:
            total = db.execute(text(count_query)).scalar()
        
        return {
            "total": total,
            "customers": customers
        }
        
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")


@router.get("/{customer_id}")
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get a single customer"""
    try:
        result = db.execute(text("""
            SELECT c.*, 
                COUNT(DISTINCT o.order_id) as total_orders,
                COALESCE(SUM(o.total_amount), 0) as total_business
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            WHERE c.customer_id = :id
            GROUP BY c.customer_id, c.customer_name
        """), {"id": customer_id})
        
        customer = result.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        return dict(customer._mapping)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.post("/")
async def create_customer(
    customer_name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new customer with minimal fields"""
    try:
        # Check what columns exist in the table
        columns_result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customers'
        """))
        columns = [row[0] for row in columns_result]
        
        # Build insert query based on available columns
        insert_fields = ["customer_name"]
        insert_values = {"customer_name": customer_name}
        
        if "phone" in columns and phone:
            insert_fields.append("phone")
            insert_values["phone"] = phone
        
        if "email" in columns and email:
            insert_fields.append("email")
            insert_values["email"] = email
        
        if "org_id" in columns:
            insert_fields.append("org_id")
            insert_values["org_id"] = DEFAULT_ORG_ID
        
        if "created_at" in columns:
            insert_fields.append("created_at")
            insert_values["created_at"] = "CURRENT_TIMESTAMP"
        
        # Build query
        fields_str = ", ".join(insert_fields)
        placeholders = ", ".join([f":{f}" if f != "created_at" else "CURRENT_TIMESTAMP" 
                                for f in insert_fields])
        
        query = f"""
            INSERT INTO customers ({fields_str})
            VALUES ({placeholders})
            RETURNING customer_id
        """
        
        # Remove created_at from values dict since we use CURRENT_TIMESTAMP
        if "created_at" in insert_values:
            del insert_values["created_at"]
        
        result = db.execute(text(query), insert_values)
        customer_id = result.scalar()
        db.commit()
        
        # Return the created customer
        return await get_customer(customer_id, db)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.get("/{customer_id}/orders")
async def get_customer_orders(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get orders for a customer"""
    try:
        # Check if customer exists
        exists = db.execute(text("""
            SELECT 1 FROM customers WHERE customer_id = :id
        """), {"id": customer_id}).scalar()
        
        if not exists:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        # Get orders
        result = db.execute(text("""
            SELECT o.*, 
                CASE 
                    WHEN o.total_amount IS NOT NULL THEN o.total_amount
                    ELSE COALESCE(SUM(oi.quantity * oi.price), 0)
                END as calculated_total
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.customer_id = :customer_id
            GROUP BY o.order_id, o.customer_id, o.order_date, o.total_amount
            ORDER BY o.order_date DESC
        """), {"customer_id": customer_id})
        
        orders = []
        for row in result:
            order_dict = dict(row._mapping)
            orders.append(order_dict)
        
        return {
            "customer_id": customer_id,
            "total_orders": len(orders),
            "orders": orders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer orders: {str(e)}")