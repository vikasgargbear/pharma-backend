"""
Collection Center API Router
Manages receivables collection and payment reminders
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from ...database import get_db
# from ...services.messaging import SMSService, WhatsAppService, EmailService  # Commented out - using click-based approach

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/collection-center", tags=["collection-center"])

# Initialize messaging services
sms_service = SMSService()
whatsapp_service = WhatsAppService()
email_service = EmailService()

@router.get("/outstanding/summary")
async def get_outstanding_summary(
    party_type: Optional[str] = Query(None, regex="^(customer|supplier)$"),
    org_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get summary of all outstanding amounts
    """
    try:
        # Base query for the appropriate table
        if party_type == "customer":
            table = "customer_outstanding"
            party_col = "customer_id"
        elif party_type == "supplier":
            table = "supplier_outstanding"
            party_col = "supplier_id"
        else:
            # Use the view for all
            query = """
                SELECT 
                    COUNT(DISTINCT party_id) as total_parties,
                    COUNT(*) as total_bills,
                    SUM(outstanding_amount) as total_outstanding,
                    SUM(CASE WHEN days_overdue <= 0 THEN outstanding_amount ELSE 0 END) as current_amount,
                    SUM(CASE WHEN days_overdue > 0 THEN outstanding_amount ELSE 0 END) as overdue_amount,
                    SUM(CASE WHEN days_overdue BETWEEN 1 AND 30 THEN outstanding_amount ELSE 0 END) as overdue_0_30,
                    SUM(CASE WHEN days_overdue BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) as overdue_31_60,
                    SUM(CASE WHEN days_overdue BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) as overdue_61_90,
                    SUM(CASE WHEN days_overdue > 90 THEN outstanding_amount ELSE 0 END) as overdue_above_90
                FROM all_outstanding
                WHERE status IN ('pending', 'partial')
            """
            params = {}
            
            if org_id:
                query += " AND org_id = :org_id"
                params["org_id"] = org_id
                
            result = db.execute(text(query), params).fetchone()
            
            return {
                "total_parties": result.total_parties or 0,
                "total_bills": result.total_bills or 0,
                "total_outstanding": float(result.total_outstanding or 0),
                "current_amount": float(result.current_amount or 0),
                "overdue_amount": float(result.overdue_amount or 0),
                "aging": {
                    "current": float(result.current_amount or 0),
                    "0_30_days": float(result.overdue_0_30 or 0),
                    "31_60_days": float(result.overdue_31_60 or 0),
                    "61_90_days": float(result.overdue_61_90 or 0),
                    "above_90_days": float(result.overdue_above_90 or 0)
                }
            }
            
        # Query for specific party type
        query = f"""
            SELECT 
                COUNT(DISTINCT {party_col}) as total_parties,
                COUNT(*) as total_bills,
                SUM(outstanding_amount) as total_outstanding,
                SUM(CASE WHEN days_overdue <= 0 THEN outstanding_amount ELSE 0 END) as current_amount,
                SUM(CASE WHEN days_overdue > 0 THEN outstanding_amount ELSE 0 END) as overdue_amount,
                SUM(CASE WHEN days_overdue BETWEEN 1 AND 30 THEN outstanding_amount ELSE 0 END) as overdue_0_30,
                SUM(CASE WHEN days_overdue BETWEEN 31 AND 60 THEN outstanding_amount ELSE 0 END) as overdue_31_60,
                SUM(CASE WHEN days_overdue BETWEEN 61 AND 90 THEN outstanding_amount ELSE 0 END) as overdue_61_90,
                SUM(CASE WHEN days_overdue > 90 THEN outstanding_amount ELSE 0 END) as overdue_above_90
            FROM {table}
            WHERE status IN ('pending', 'partial')
        """
        params = {}
        
        if org_id:
            query += " AND org_id = :org_id"
            params["org_id"] = org_id
            
        result = db.execute(text(query), params).fetchone()
        
        return {
            "party_type": party_type,
            "total_parties": result.total_parties or 0,
            "total_bills": result.total_bills or 0,
            "total_outstanding": float(result.total_outstanding or 0),
            "current_amount": float(result.current_amount or 0),
            "overdue_amount": float(result.overdue_amount or 0),
            "aging": {
                "current": float(result.current_amount or 0),
                "0_30_days": float(result.overdue_0_30 or 0),
                "31_60_days": float(result.overdue_31_60 or 0),
                "61_90_days": float(result.overdue_61_90 or 0),
                "above_90_days": float(result.overdue_above_90 or 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching outstanding summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outstanding/list")
async def get_outstanding_list(
    party_type: str = Query(..., regex="^(customer|supplier)$"),
    status: Optional[str] = Query(None, regex="^(pending|partial|paid)$"),
    min_days_overdue: Optional[int] = None,
    max_days_overdue: Optional[int] = None,
    min_amount: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get list of outstanding bills with filters
    """
    try:
        # Determine table and columns
        if party_type == "customer":
            table = "customer_outstanding"
            party_col = "customer_id"
            party_table = "customers"
            party_name_col = "customer_name"
        else:
            table = "supplier_outstanding"
            party_col = "supplier_id"
            party_table = "suppliers"
            party_name_col = "supplier_name"
            
        # Build query
        query = f"""
            SELECT 
                o.*,
                p.{party_name_col} as party_name,
                p.phone,
                p.email
            FROM {table} o
            JOIN {party_table} p ON o.{party_col} = p.{party_col}
            WHERE 1=1
        """
        params = {"skip": skip, "limit": limit}
        
        # Add filters
        if status:
            query += " AND o.status = :status"
            params["status"] = status
        else:
            query += " AND o.status IN ('pending', 'partial')"
            
        if min_days_overdue is not None:
            query += " AND o.days_overdue >= :min_days"
            params["min_days"] = min_days_overdue
            
        if max_days_overdue is not None:
            query += " AND o.days_overdue <= :max_days"
            params["max_days"] = max_days_overdue
            
        if min_amount is not None:
            query += " AND o.outstanding_amount >= :min_amount"
            params["min_amount"] = min_amount
            
        # Order and pagination
        query += " ORDER BY o.days_overdue DESC, o.outstanding_amount DESC LIMIT :limit OFFSET :skip"
        
        results = db.execute(text(query), params).fetchall()
        
        # Format results
        outstanding_list = []
        for row in results:
            outstanding_list.append({
                "outstanding_id": row.outstanding_id,
                "party_id": getattr(row, party_col),
                "party_name": row.party_name,
                "phone": row.phone,
                "email": row.email,
                "invoice_number": row.invoice_number,
                "invoice_date": row.invoice_date,
                "due_date": row.due_date,
                "total_amount": float(row.total_amount),
                "paid_amount": float(row.paid_amount),
                "outstanding_amount": float(row.outstanding_amount),
                "days_overdue": row.days_overdue,
                "status": row.status,
                "aging_bucket": _get_aging_bucket(row.days_overdue)
            })
            
        return {
            "party_type": party_type,
            "count": len(outstanding_list),
            "outstanding": outstanding_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching outstanding list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminders/generate-links")
async def generate_reminder_links(
    reminder_data: dict,
    db: Session = Depends(get_db)
):
    """
    Generate clickable WhatsApp/SMS links for payment reminders
    """
    try:
        import urllib.parse
        
        # Validate required fields
        required_fields = ["party_type", "party_ids", "channel", "message"]
        for field in required_fields:
            if field not in reminder_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        party_type = reminder_data["party_type"]
        party_ids = reminder_data["party_ids"]
        channel = reminder_data["channel"]  # 'sms', 'whatsapp'
        message_template = reminder_data["message"]
        
        # Get party details and outstanding
        if party_type == "customer":
            party_query = """
                SELECT 
                    c.customer_id as party_id,
                    c.customer_name as party_name,
                    c.phone,
                    c.email,
                    SUM(o.outstanding_amount) as total_outstanding,
                    COUNT(o.outstanding_id) as bill_count,
                    MAX(o.days_overdue) as max_days_overdue,
                    STRING_AGG(o.invoice_number, ', ') as invoice_numbers
                FROM customers c
                JOIN customer_outstanding o ON c.customer_id = o.customer_id
                WHERE c.customer_id = ANY(:party_ids)
                GROUP BY c.customer_id, c.customer_name, c.phone, c.email
            """
        else:  # supplier
            party_query = """
                SELECT 
                    s.supplier_id as party_id,
                    s.supplier_name as party_name,
                    s.phone,
                    s.email,
                    SUM(o.outstanding_amount) as total_outstanding,
                    COUNT(o.outstanding_id) as bill_count,
                    MAX(o.days_overdue) as max_days_overdue,
                    STRING_AGG(o.bill_number, ', ') as invoice_numbers
                FROM suppliers s
                JOIN supplier_outstanding o ON s.supplier_id = o.supplier_id
                WHERE s.supplier_id = ANY(:party_ids)
                GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email
            """
            
        parties = db.execute(
            text(party_query),
            {"party_ids": party_ids}
        ).fetchall()
        
        links = []
        
        for party in parties:
            # Prepare message with variables
            message = message_template.replace("{{party_name}}", party.party_name)
            message = message.replace("{{amount}}", f"₹{party.total_outstanding:.2f}")
            message = message.replace("{{days_overdue}}", str(party.max_days_overdue))
            message = message.replace("{{invoice_numbers}}", party.invoice_numbers or "")
            message = message.replace("{{company_name}}", "AASO Pharmaceuticals")
            
            if not party.phone:
                continue
                
            # Clean phone number (remove spaces, dashes)
            phone = party.phone.replace(" ", "").replace("-", "")
            if not phone.startswith("+"):
                # Assume Indian number if no country code
                if not phone.startswith("91"):
                    phone = "91" + phone
                phone = "+" + phone
            
            link = ""
            if channel == "whatsapp":
                # Generate WhatsApp link
                encoded_message = urllib.parse.quote(message)
                link = f"https://wa.me/{phone}?text={encoded_message}"
            elif channel == "sms":
                # Generate SMS link
                encoded_message = urllib.parse.quote(message)
                link = f"sms:{phone}?body={encoded_message}"
                
            links.append({
                "party_id": party.party_id,
                "party_name": party.party_name,
                "phone": party.phone,
                "outstanding_amount": float(party.total_outstanding),
                "days_overdue": party.max_days_overdue,
                "link": link,
                "message": message
            })
            
        return {
            "status": "success",
            "channel": channel,
            "links": links,
            "count": len(links)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating reminder links: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reminders/send")
async def send_reminders(
    reminder_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send payment reminders via SMS/WhatsApp/Email (Deprecated - use generate-links instead)
    """
    try:
        # Validate required fields
        required_fields = ["party_type", "party_ids", "channel", "message"]
        for field in required_fields:
            if field not in reminder_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        party_type = reminder_data["party_type"]
        party_ids = reminder_data["party_ids"]
        channel = reminder_data["channel"]  # 'sms', 'whatsapp', 'email'
        message_template = reminder_data["message"]
        
        # Get party details and outstanding
        if party_type == "customer":
            party_query = """
                SELECT 
                    c.customer_id as party_id,
                    c.customer_name as party_name,
                    c.phone,
                    c.email,
                    SUM(o.outstanding_amount) as total_outstanding,
                    COUNT(o.outstanding_id) as bill_count,
                    STRING_AGG(o.invoice_number, ', ') as invoice_numbers,
                    MAX(o.days_overdue) as max_days_overdue
                FROM customers c
                JOIN customer_outstanding o ON c.customer_id = o.customer_id
                WHERE c.customer_id = ANY(:party_ids)
                AND o.status IN ('pending', 'partial')
                GROUP BY c.customer_id, c.customer_name, c.phone, c.email
            """
        else:
            party_query = """
                SELECT 
                    s.supplier_id as party_id,
                    s.supplier_name as party_name,
                    s.phone,
                    s.email,
                    SUM(o.outstanding_amount) as total_outstanding,
                    COUNT(o.outstanding_id) as bill_count,
                    STRING_AGG(o.invoice_number, ', ') as invoice_numbers,
                    MAX(o.days_overdue) as max_days_overdue
                FROM suppliers s
                JOIN supplier_outstanding o ON s.supplier_id = o.supplier_id
                WHERE s.supplier_id = ANY(:party_ids)
                AND o.status IN ('pending', 'partial')
                GROUP BY s.supplier_id, s.supplier_name, s.phone, s.email
            """
            
        parties = db.execute(text(party_query), {"party_ids": party_ids}).fetchall()
        
        # Send reminders
        sent_count = 0
        failed_count = 0
        
        for party in parties:
            # Prepare message with variables
            message = message_template.replace("{{party_name}}", party.party_name)
            message = message.replace("{{amount}}", f"{party.total_outstanding:.2f}")
            message = message.replace("{{days_overdue}}", str(party.max_days_overdue))
            message = message.replace("{{invoice_numbers}}", party.invoice_numbers or "")
            message = message.replace("{{company_name}}", "AASO Pharmaceuticals")
            
            # Create reminder record
            reminder_result = db.execute(
                text("""
                    INSERT INTO collection_reminders (
                        org_id, customer_id, reminder_type,
                        reminder_date, message_content
                    ) VALUES (
                        :org_id, :customer_id, :reminder_type,
                        :reminder_date, :message_content
                    )
                    RETURNING reminder_id
                """),
                {
                    "org_id": reminder_data.get("org_id", "12de5e22-eee7-4d25-b3a7-d16d01c6170f"),
                    "customer_id": party.party_id,
                    "reminder_type": channel,
                    "reminder_date": date.today(),
                    "message_content": message
                }
            ).fetchone()
            
            reminder_id = reminder_result.reminder_id
            
            # Send via appropriate channel
            if channel == "sms" and party.phone:
                background_tasks.add_task(
                    _send_sms_reminder,
                    db, reminder_id, party.phone, message
                )
                sent_count += 1
                
            elif channel == "whatsapp" and party.phone:
                background_tasks.add_task(
                    _send_whatsapp_reminder,
                    db, reminder_id, party.phone, message
                )
                sent_count += 1
                
            elif channel == "email" and party.email:
                subject = f"Payment Reminder - Outstanding Amount ₹{party.total_outstanding:.2f}"
                background_tasks.add_task(
                    _send_email_reminder,
                    db, reminder_id, party.email, subject, message
                )
                sent_count += 1
            else:
                failed_count += 1
                
        db.commit()
        
        return {
            "status": "success",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "message": f"Reminders queued for {sent_count} parties"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminders/history")
async def get_reminder_history(
    customer_id: Optional[int] = None,
    reminder_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get history of sent reminders
    """
    try:
        query = """
            SELECT 
                r.*,
                c.customer_name,
                c.phone,
                c.email
            FROM collection_reminders r
            JOIN customers c ON r.customer_id = c.customer_id
            WHERE 1=1
        """
        params = {"skip": skip, "limit": limit}
        
        if customer_id:
            query += " AND r.customer_id = :customer_id"
            params["customer_id"] = customer_id
            
        if reminder_type:
            query += " AND r.reminder_type = :reminder_type"
            params["reminder_type"] = reminder_type
            
        if from_date:
            query += " AND r.reminder_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            query += " AND r.reminder_date <= :to_date"
            params["to_date"] = to_date
            
        query += " ORDER BY r.created_at DESC LIMIT :limit OFFSET :skip"
        
        reminders = db.execute(text(query), params).fetchall()
        
        return {
            "count": len(reminders),
            "reminders": [
                {
                    "reminder_id": r.reminder_id,
                    "customer_id": r.customer_id,
                    "customer_name": r.customer_name,
                    "phone": r.phone,
                    "email": r.email,
                    "reminder_type": r.reminder_type,
                    "reminder_date": r.reminder_date,
                    "message": r.message_content,
                    "status": r.status,
                    "response_received": r.response_received,
                    "response_type": r.response_type,
                    "response_notes": r.response_notes,
                    "created_at": r.created_at
                }
                for r in reminders
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching reminder history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promises")
async def create_payment_promise(
    promise_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a payment promise from customer
    """
    try:
        # Validate required fields
        required_fields = ["customer_id", "promise_date", "promised_amount"]
        for field in required_fields:
            if field not in promise_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        # Create promise
        result = db.execute(
            text("""
                INSERT INTO payment_promises (
                    org_id, customer_id, promise_date,
                    promised_amount, source_type, source_id,
                    notes
                ) VALUES (
                    :org_id, :customer_id, :promise_date,
                    :promised_amount, :source_type, :source_id,
                    :notes
                )
                RETURNING promise_id
            """),
            {
                "org_id": promise_data.get("org_id", "12de5e22-eee7-4d25-b3a7-d16d01c6170f"),
                "customer_id": promise_data["customer_id"],
                "promise_date": promise_data["promise_date"],
                "promised_amount": Decimal(str(promise_data["promised_amount"])),
                "source_type": promise_data.get("source_type", "manual"),
                "source_id": promise_data.get("source_id"),
                "notes": promise_data.get("notes")
            }
        ).fetchone()
        
        # Update reminder if linked
        if promise_data.get("reminder_id"):
            db.execute(
                text("""
                    UPDATE collection_reminders
                    SET response_received = TRUE,
                        response_type = 'promise',
                        response_date = CURRENT_TIMESTAMP,
                        response_notes = :notes
                    WHERE reminder_id = :reminder_id
                """),
                {
                    "reminder_id": promise_data["reminder_id"],
                    "notes": f"Promise for ₹{promise_data['promised_amount']} on {promise_data['promise_date']}"
                }
            )
            
        db.commit()
        
        return {
            "status": "success",
            "promise_id": result.promise_id,
            "message": "Payment promise recorded successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment promise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/promises")
async def get_payment_promises(
    status: Optional[str] = Query(None, regex="^(pending|partial|fulfilled|broken)$"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get payment promises with filters
    """
    try:
        query = """
            SELECT 
                p.*,
                c.customer_name,
                c.phone
            FROM payment_promises p
            JOIN customers c ON p.customer_id = c.customer_id
            WHERE 1=1
        """
        params = {}
        
        if status:
            query += " AND p.status = :status"
            params["status"] = status
            
        if from_date:
            query += " AND p.promise_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            query += " AND p.promise_date <= :to_date"
            params["to_date"] = to_date
            
        query += " ORDER BY p.promise_date, p.created_at DESC"
        
        promises = db.execute(text(query), params).fetchall()
        
        return {
            "count": len(promises),
            "promises": [
                {
                    "promise_id": p.promise_id,
                    "customer_id": p.customer_id,
                    "customer_name": p.customer_name,
                    "phone": p.phone,
                    "promise_date": p.promise_date,
                    "promised_amount": float(p.promised_amount),
                    "paid_amount": float(p.paid_amount),
                    "status": p.status,
                    "source_type": p.source_type,
                    "notes": p.notes,
                    "created_at": p.created_at
                }
                for p in promises
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching payment promises: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/promises/{promise_id}/fulfill")
async def fulfill_promise(
    promise_id: int,
    fulfillment_data: dict,
    db: Session = Depends(get_db)
):
    """
    Mark a promise as fulfilled or partially fulfilled
    """
    try:
        # Get promise
        promise = db.execute(
            text("SELECT * FROM payment_promises WHERE promise_id = :promise_id"),
            {"promise_id": promise_id}
        ).fetchone()
        
        if not promise:
            raise HTTPException(status_code=404, detail="Promise not found")
            
        # Update promise
        paid_amount = Decimal(str(fulfillment_data.get("paid_amount", 0)))
        new_total_paid = promise.paid_amount + paid_amount
        
        if new_total_paid >= promise.promised_amount:
            status = "fulfilled"
        else:
            status = "partial"
            
        db.execute(
            text("""
                UPDATE payment_promises
                SET paid_amount = paid_amount + :paid_amount,
                    status = :status,
                    payment_date = :payment_date,
                    payment_reference = :payment_reference,
                    updated_at = CURRENT_TIMESTAMP
                WHERE promise_id = :promise_id
            """),
            {
                "promise_id": promise_id,
                "paid_amount": paid_amount,
                "status": status,
                "payment_date": fulfillment_data.get("payment_date", date.today()),
                "payment_reference": fulfillment_data.get("payment_reference")
            }
        )
        
        db.commit()
        
        return {
            "status": "success",
            "promise_status": status,
            "message": f"Promise {status}"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error fulfilling promise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def _get_aging_bucket(days_overdue: int) -> str:
    """Get aging bucket for days overdue"""
    if days_overdue <= 0:
        return "Current"
    elif days_overdue <= 30:
        return "0-30 days"
    elif days_overdue <= 60:
        return "31-60 days"
    elif days_overdue <= 90:
        return "61-90 days"
    else:
        return ">90 days"

async def _send_sms_reminder(db: Session, reminder_id: int, phone: str, message: str):
    """Send SMS reminder"""
    try:
        # Queue SMS
        result = db.execute(
            text("""
                INSERT INTO sms_queue (
                    to_phone, message, reference_type, reference_id
                ) VALUES (
                    :phone, :message, 'collection_reminder', :reminder_id
                )
                RETURNING sms_id
            """),
            {
                "phone": phone,
                "message": message,
                "reminder_id": str(reminder_id)
            }
        ).fetchone()
        
        # Update reminder status
        db.execute(
            text("""
                UPDATE collection_reminders
                SET status = 'sent',
                    message_id = :message_id
                WHERE reminder_id = :reminder_id
            """),
            {
                "reminder_id": reminder_id,
                "message_id": result.sms_id
            }
        )
        
        db.commit()
        
        # Actually send SMS (would call SMS provider API)
        # sms_service.send(phone, message)
        
    except Exception as e:
        logger.error(f"Error sending SMS reminder: {e}")
        db.rollback()

async def _send_whatsapp_reminder(db: Session, reminder_id: int, phone: str, message: str):
    """Send WhatsApp reminder"""
    try:
        # Queue WhatsApp message
        result = db.execute(
            text("""
                INSERT INTO whatsapp_queue (
                    to_phone, message_type, content,
                    reference_type, reference_id
                ) VALUES (
                    :phone, 'text', :message,
                    'collection_reminder', :reminder_id
                )
                RETURNING whatsapp_id
            """),
            {
                "phone": phone,
                "message": message,
                "reminder_id": str(reminder_id)
            }
        ).fetchone()
        
        # Update reminder status
        db.execute(
            text("""
                UPDATE collection_reminders
                SET status = 'sent',
                    message_id = :message_id
                WHERE reminder_id = :reminder_id
            """),
            {
                "reminder_id": reminder_id,
                "message_id": result.whatsapp_id
            }
        )
        
        db.commit()
        
        # Actually send WhatsApp (would call WhatsApp Business API)
        # whatsapp_service.send(phone, message)
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp reminder: {e}")
        db.rollback()

async def _send_email_reminder(db: Session, reminder_id: int, email: str, subject: str, message: str):
    """Send email reminder"""
    try:
        # Queue email
        result = db.execute(
            text("""
                INSERT INTO email_queue (
                    to_email, subject, body_text, status
                ) VALUES (
                    ARRAY[:email], :subject, :message, 'pending'
                )
                RETURNING email_id
            """),
            {
                "email": email,
                "subject": subject,
                "message": message
            }
        ).fetchone()
        
        # Update reminder status
        db.execute(
            text("""
                UPDATE collection_reminders
                SET status = 'sent',
                    message_id = :message_id
                WHERE reminder_id = :reminder_id
            """),
            {
                "reminder_id": reminder_id,
                "message_id": result.email_id
            }
        )
        
        db.commit()
        
        # Email will be sent by email queue processor
        
    except Exception as e:
        logger.error(f"Error sending email reminder: {e}")
        db.rollback()