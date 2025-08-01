"""
Customer API - Works with new database schema
Handles parties.customers table with proper column names
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from ...database import get_db
from ...schemas_v2.customer import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])

# Default org_id (same as in original customers.py)
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new customer - using new schema
    Maps old field names to new database columns
    """
    try:
        # Generate customer code
        result = db.execute(text("""
            SELECT 'CUST' || LPAD(COALESCE(MAX(SUBSTRING(customer_code FROM '[0-9]+$')::INTEGER), 0) + 1::TEXT, 5, '0')
            FROM parties.customers
            WHERE customer_code LIKE 'CUST%'
        """))
        customer_code = result.scalar()
        
        # Map old field names to new schema
        query = text("""
            INSERT INTO parties.customers (
                org_id, customer_code, customer_name, customer_type,
                primary_phone, primary_email, secondary_phone,
                contact_person_name, gst_number, pan_number,
                drug_license_number, credit_limit, credit_days,
                internal_notes, is_active
            ) VALUES (
                :org_id, :customer_code, :customer_name, :customer_type,
                :primary_phone, :primary_email, :secondary_phone,
                :contact_person_name, :gst_number, :pan_number,
                :drug_license_number, :credit_limit, :credit_days,
                :internal_notes, :is_active
            ) RETURNING customer_id
        """)
        
        # Map fields from old format to new format
        customer_data = {
            "org_id": getattr(customer, 'org_id', DEFAULT_ORG_ID) or DEFAULT_ORG_ID,
            "customer_code": customer_code,
            "customer_name": customer.customer_name,
            "customer_type": customer.customer_type or "retail",
            "primary_phone": customer.phone,  # Map phone -> primary_phone
            "primary_email": customer.email,
            "secondary_phone": customer.alternate_phone,  # Map alternate_phone -> secondary_phone
            "contact_person_name": customer.contact_person,  # Map contact_person -> contact_person_name
            "gst_number": customer.gstin,  # Map gstin -> gst_number
            "pan_number": customer.pan_number,
            "drug_license_number": customer.drug_license_number,
            "credit_limit": customer.credit_limit or 0,
            "credit_days": customer.credit_days or 0,
            "internal_notes": customer.notes,  # Map notes -> internal_notes
            "is_active": customer.is_active if hasattr(customer, 'is_active') else True
        }
        
        result = db.execute(query, customer_data)
        customer_id = result.scalar()
        
        # Create address if provided
        if any([customer.address_line1, customer.city, customer.state]):
            address_query = text("""
                INSERT INTO parties.customer_addresses (
                    customer_id, address_type, 
                    address_line1, address_line2, area_name,
                    city, state, pincode, 
                    is_primary, is_billing, is_shipping, is_active
                ) VALUES (
                    :customer_id, 'billing',
                    :address_line1, :address_line2, :area_name,
                    :city, :state, :pincode,
                    true, true, false, true
                )
            """)
            
            address_data = {
                "customer_id": customer_id,
                "address_line1": customer.address_line1 or '',
                "address_line2": customer.address_line2,
                "area_name": customer.area,  # Map area -> area_name
                "city": customer.city or '',
                "state": customer.state or '',
                "pincode": customer.pincode or '000000'
            }
            
            db.execute(address_query, address_data)
        
        db.commit()
        
        # Return created customer
        return await get_customer(customer_id, db)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer details - maps new schema to old format"""
    try:
        query = text("""
            SELECT 
                c.customer_id,
                c.org_id,
                c.customer_code,
                c.customer_name,
                c.customer_type,
                c.primary_phone as phone,  -- Map back to old name
                c.primary_email as email,
                c.secondary_phone as alternate_phone,
                c.contact_person_name as contact_person,
                c.gst_number as gstin,
                c.pan_number,
                c.drug_license_number,
                c.credit_limit,
                c.credit_days,
                0 as discount_percent,  -- TODO: Calculate from discount_group_id
                c.internal_notes as notes,
                c.is_active,
                c.created_at,
                c.updated_at,
                -- Metrics
                COALESCE(c.current_outstanding, 0) as outstanding_amount,
                COALESCE(c.total_business_amount, 0) as total_business,
                COALESCE(c.total_transactions, 0) as total_orders,
                c.last_transaction_date as last_order_date,
                -- Address from primary address
                a.address_line1,
                a.address_line2,
                a.area_name as area,
                a.city,
                a.state,
                a.pincode
            FROM parties.customers c
            LEFT JOIN parties.customer_addresses a ON c.customer_id = a.customer_id 
                AND a.is_primary = true AND a.is_active = true
            WHERE c.customer_id = :customer_id
            AND c.org_id = :org_id
        """)
        
        result = db.execute(query, {"customer_id": customer_id, "org_id": DEFAULT_ORG_ID})
        customer = result.fetchone()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return CustomerResponse(**dict(customer._mapping))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    customer_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    city: Optional[str] = None,
    has_gstin: Optional[bool] = None,
    include_stats: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List customers with search and filters"""
    try:
        # Build query
        base_query = """
            SELECT 
                c.customer_id,
                c.org_id,
                c.customer_code,
                c.customer_name,
                c.customer_type,
                c.primary_phone as phone,
                c.primary_email as email,
                c.secondary_phone as alternate_phone,
                c.contact_person_name as contact_person,
                c.gst_number as gstin,
                c.pan_number,
                c.drug_license_number,
                c.credit_limit,
                c.credit_days,
                0 as discount_percent,
                c.internal_notes as notes,
                c.is_active,
                c.created_at,
                c.updated_at
        """
        
        if include_stats:
            base_query += """,
                COALESCE(c.current_outstanding, 0) as outstanding_amount,
                COALESCE(c.total_business_amount, 0) as total_business,
                COALESCE(c.total_transactions, 0) as total_orders,
                c.last_transaction_date as last_order_date
            """
        else:
            base_query += """,
                0 as outstanding_amount,
                0 as total_business,
                0 as total_orders,
                NULL as last_order_date
            """
        
        base_query += """,
                a.address_line1,
                a.address_line2,
                a.area_name as area,
                a.city,
                a.state,
                a.pincode
            FROM parties.customers c
            LEFT JOIN parties.customer_addresses a ON c.customer_id = a.customer_id 
                AND a.is_primary = true AND a.is_active = true
            WHERE c.org_id = :org_id
        """
        
        count_query = """
            SELECT COUNT(*)
            FROM parties.customers c
            WHERE c.org_id = :org_id
        """
        
        params = {"org_id": DEFAULT_ORG_ID}
        
        # Add filters
        if search:
            search_filter = """ AND (
                c.customer_name ILIKE :search OR
                c.customer_code ILIKE :search OR
                c.primary_phone ILIKE :search OR
                c.gst_number ILIKE :search OR
                a.area_name ILIKE :search OR
                a.city ILIKE :search
            )"""
            base_query += search_filter
            count_query += search_filter.replace("a.area_name", "''").replace("a.city", "''")
            params["search"] = f"%{search}%"
        
        if customer_type:
            filter_clause = " AND c.customer_type = :customer_type"
            base_query += filter_clause
            count_query += filter_clause
            params["customer_type"] = customer_type
        
        if is_active is not None:
            filter_clause = " AND c.is_active = :is_active"
            base_query += filter_clause
            count_query += filter_clause
            params["is_active"] = is_active
        
        if city:
            base_query += " AND a.city ILIKE :city"
            params["city"] = f"%{city}%"
        
        if has_gstin is not None:
            if has_gstin:
                filter_clause = " AND c.gst_number IS NOT NULL"
            else:
                filter_clause = " AND c.gst_number IS NULL"
            base_query += filter_clause
            count_query += filter_clause
        
        # Get total count
        total = db.execute(text(count_query), params).scalar()
        
        # Add ordering and pagination
        base_query += " ORDER BY c.customer_name LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Execute query
        result = db.execute(text(base_query), params)
        customers = []
        
        for row in result:
            customer_dict = dict(row._mapping)
            customers.append(CustomerResponse(**customer_dict))
        
        return CustomerListResponse(
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            customers=customers
        )
        
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update customer - maps old fields to new"""
    try:
        # Check if customer exists
        exists = db.execute(text("""
            SELECT 1 FROM parties.customers 
            WHERE customer_id = :customer_id AND org_id = :org_id
        """), {"customer_id": customer_id, "org_id": DEFAULT_ORG_ID}).scalar()
        
        if not exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Build update query
        update_fields = []
        params = {"customer_id": customer_id, "org_id": DEFAULT_ORG_ID}
        
        # Map old field names to new
        field_mapping = {
            "customer_name": "customer_name",
            "customer_type": "customer_type",
            "phone": "primary_phone",
            "email": "primary_email", 
            "alternate_phone": "secondary_phone",
            "contact_person": "contact_person_name",
            "gstin": "gst_number",
            "pan_number": "pan_number",
            "drug_license_number": "drug_license_number",
            "credit_limit": "credit_limit",
            "credit_days": "credit_days",
            "notes": "internal_notes",
            "is_active": "is_active"
        }
        
        for old_field, new_field in field_mapping.items():
            if hasattr(customer_update, old_field):
                value = getattr(customer_update, old_field)
                if value is not None:
                    update_fields.append(f"{new_field} = :{old_field}")
                    params[old_field] = value
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE parties.customers 
                SET {', '.join(update_fields)}
                WHERE customer_id = :customer_id AND org_id = :org_id
            """
            
            db.execute(text(query), params)
            
            # Update address if provided
            if any([hasattr(customer_update, f) and getattr(customer_update, f) is not None 
                    for f in ["address_line1", "address_line2", "area", "city", "state", "pincode"]]):
                
                # Check if address exists
                addr_exists = db.execute(text("""
                    SELECT 1 FROM parties.customer_addresses
                    WHERE customer_id = :customer_id AND is_primary = true
                """), {"customer_id": customer_id}).scalar()
                
                if addr_exists:
                    # Update existing
                    addr_fields = []
                    addr_params = {"customer_id": customer_id}
                    
                    addr_mapping = {
                        "address_line1": "address_line1",
                        "address_line2": "address_line2",
                        "area": "area_name",
                        "city": "city",
                        "state": "state",
                        "pincode": "pincode"
                    }
                    
                    for old_field, new_field in addr_mapping.items():
                        if hasattr(customer_update, old_field):
                            value = getattr(customer_update, old_field)
                            if value is not None:
                                addr_fields.append(f"{new_field} = :{old_field}")
                                addr_params[old_field] = value
                    
                    if addr_fields:
                        addr_query = f"""
                            UPDATE parties.customer_addresses
                            SET {', '.join(addr_fields)}
                            WHERE customer_id = :customer_id AND is_primary = true
                        """
                        db.execute(text(addr_query), addr_params)
                
            db.commit()
        
        # Return updated customer
        return await get_customer(customer_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")


# Additional endpoints for compatibility
@router.get("/{customer_id}/outstanding")
async def get_customer_outstanding(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer outstanding details"""
    try:
        query = text("""
            SELECT 
                c.customer_id,
                c.customer_name,
                c.credit_limit,
                c.credit_days,
                COALESCE(c.current_outstanding, 0) as current_outstanding,
                c.credit_limit - COALESCE(c.current_outstanding, 0) as available_credit
            FROM parties.customers c
            WHERE c.customer_id = :customer_id
            AND c.org_id = :org_id
        """)
        
        result = db.execute(query, {"customer_id": customer_id, "org_id": DEFAULT_ORG_ID})
        outstanding = result.fetchone()
        
        if not outstanding:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return dict(outstanding._mapping)
        
    except Exception as e:
        logger.error(f"Error getting customer outstanding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer outstanding: {str(e)}")