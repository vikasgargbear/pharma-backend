"""
Party Ledger API Router
Handles party-wise ledger entries and due tracking
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/party-ledger", tags=["party-ledger"])

@router.get("/")
async def get_party_ledger(
    party_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get ledger entries for a specific party
    """
    try:
        # Get party details
        party = db.execute(
            text("SELECT * FROM parties WHERE party_id = :party_id"),
            {"party_id": party_id}
        ).first()
        
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")
            
        # Calculate opening balance (before from_date if provided)
        opening_balance = Decimal("0")
        if from_date:
            opening_query = """
                SELECT 
                    COALESCE(SUM(debit_amount), 0) - COALESCE(SUM(credit_amount), 0) as balance
                FROM party_ledger
                WHERE party_id = :party_id
                AND transaction_date < :from_date
            """
            opening_balance = db.execute(
                text(opening_query),
                {"party_id": party_id, "from_date": from_date}
            ).scalar() or Decimal("0")
            
        # Get ledger entries
        ledger_query = """
            SELECT 
                pl.*,
                CASE 
                    WHEN pl.reference_type = 'sale' THEN s.invoice_number
                    WHEN pl.reference_type = 'purchase' THEN p.purchase_number
                    WHEN pl.reference_type = 'payment' THEN py.payment_number
                    WHEN pl.reference_type = 'receipt' THEN r.receipt_number
                    WHEN pl.reference_type = 'sale_return' THEN sr.return_number
                    WHEN pl.reference_type = 'purchase_return' THEN pr.return_number
                    WHEN pl.reference_type = 'credit_note' THEN cn.note_number
                    WHEN pl.reference_type = 'debit_note' THEN dn.note_number
                    ELSE NULL
                END as reference_number
            FROM party_ledger pl
            LEFT JOIN sales s ON pl.reference_type = 'sale' AND pl.reference_id = s.sale_id
            LEFT JOIN purchases p ON pl.reference_type = 'purchase' AND pl.reference_id = p.purchase_id
            LEFT JOIN payments py ON pl.reference_type = 'payment' AND pl.reference_id = py.payment_id
            LEFT JOIN receipts r ON pl.reference_type = 'receipt' AND pl.reference_id = r.receipt_id
            LEFT JOIN sale_returns sr ON pl.reference_type = 'sale_return' AND pl.reference_id = sr.return_id
            LEFT JOIN purchase_returns pr ON pl.reference_type = 'purchase_return' AND pl.reference_id = pr.return_id
            LEFT JOIN credit_notes cn ON pl.reference_type = 'credit_note' AND pl.reference_id = cn.note_id
            LEFT JOIN debit_notes dn ON pl.reference_type = 'debit_note' AND pl.reference_id = dn.note_id
            WHERE pl.party_id = :party_id
        """
        
        params = {"party_id": party_id}
        
        if from_date:
            ledger_query += " AND pl.transaction_date >= :from_date"
            params["from_date"] = from_date
            
        if to_date:
            ledger_query += " AND pl.transaction_date <= :to_date"
            params["to_date"] = to_date
            
        ledger_query += " ORDER BY pl.transaction_date, pl.created_at"
        
        entries = db.execute(text(ledger_query), params).fetchall()
        
        # Calculate running balance
        ledger_entries = []
        running_balance = opening_balance
        
        for entry in entries:
            running_balance += entry.debit_amount - entry.credit_amount
            entry_dict = dict(entry._mapping)
            entry_dict["running_balance"] = float(running_balance)
            ledger_entries.append(entry_dict)
            
        # Calculate closing balance
        closing_balance = running_balance
        
        # Get current outstanding
        outstanding_query = """
            SELECT 
                COALESCE(SUM(debit_amount), 0) - COALESCE(SUM(credit_amount), 0) as balance
            FROM party_ledger
            WHERE party_id = :party_id
        """
        current_outstanding = db.execute(
            text(outstanding_query),
            {"party_id": party_id}
        ).scalar() or Decimal("0")
        
        return {
            "party": dict(party._mapping),
            "opening_balance": float(opening_balance),
            "closing_balance": float(closing_balance),
            "current_outstanding": float(current_outstanding),
            "entries": ledger_entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching party ledger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outstanding")
async def get_outstanding_parties(
    party_type: Optional[str] = Query(None, description="customer/supplier/all"),
    min_amount: Optional[float] = None,
    days_overdue: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get parties with outstanding balances
    """
    try:
        query = """
            SELECT 
                p.party_id,
                p.party_name,
                p.party_type,
                p.phone,
                p.email,
                p.credit_limit,
                p.credit_days,
                COALESCE(SUM(pl.debit_amount), 0) - COALESCE(SUM(pl.credit_amount), 0) as outstanding_amount,
                MAX(pl.transaction_date) as last_transaction_date,
                MIN(CASE 
                    WHEN pl.debit_amount > 0 AND pl.due_date IS NOT NULL 
                    THEN pl.due_date 
                    ELSE NULL 
                END) as oldest_due_date
            FROM parties p
            LEFT JOIN party_ledger pl ON p.party_id = pl.party_id
            WHERE 1=1
        """
        
        params = {"skip": skip, "limit": limit}
        
        if party_type and party_type != "all":
            query += " AND p.party_type = :party_type"
            params["party_type"] = party_type
            
        query += " GROUP BY p.party_id"
        
        # Having clause for filters
        having_conditions = []
        
        having_conditions.append("COALESCE(SUM(pl.debit_amount), 0) - COALESCE(SUM(pl.credit_amount), 0) != 0")
        
        if min_amount:
            having_conditions.append("ABS(COALESCE(SUM(pl.debit_amount), 0) - COALESCE(SUM(pl.credit_amount), 0)) >= :min_amount")
            params["min_amount"] = min_amount
            
        if having_conditions:
            query += " HAVING " + " AND ".join(having_conditions)
            
        query += " ORDER BY outstanding_amount DESC LIMIT :limit OFFSET :skip"
        
        parties = db.execute(text(query), params).fetchall()
        
        # Process results to add ageing info
        result = []
        current_date = datetime.now().date()
        
        for party in parties:
            party_dict = dict(party._mapping)
            
            # Calculate days overdue if oldest_due_date exists
            if party.oldest_due_date:
                days_past_due = (current_date - party.oldest_due_date).days
                party_dict["days_overdue"] = max(0, days_past_due)
            else:
                party_dict["days_overdue"] = 0
                
            # Filter by days_overdue if specified
            if days_overdue is None or party_dict["days_overdue"] >= days_overdue:
                # Get ageing buckets
                ageing = await get_party_ageing(party.party_id, db)
                party_dict["ageing"] = ageing
                result.append(party_dict)
                
        # Get total count
        count_query = query.replace("SELECT p.party_id,", "SELECT COUNT(DISTINCT p.party_id)")
        count_query = count_query.split("ORDER BY")[0]
        total = db.execute(text(count_query), params).scalar()
        
        return {
            "total": total,
            "parties": result
        }
        
    except Exception as e:
        logger.error(f"Error fetching outstanding parties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_party_ageing(party_id: str, db: Session):
    """
    Calculate ageing buckets for a party
    """
    try:
        current_date = datetime.now().date()
        
        ageing_query = """
            SELECT 
                SUM(CASE 
                    WHEN CURRENT_DATE - pl.transaction_date <= 30 
                    THEN pl.debit_amount - pl.credit_amount 
                    ELSE 0 
                END) as current_bucket,
                SUM(CASE 
                    WHEN CURRENT_DATE - pl.transaction_date > 30 
                    AND CURRENT_DATE - pl.transaction_date <= 60 
                    THEN pl.debit_amount - pl.credit_amount 
                    ELSE 0 
                END) as days_30_60,
                SUM(CASE 
                    WHEN CURRENT_DATE - pl.transaction_date > 60 
                    AND CURRENT_DATE - pl.transaction_date <= 90 
                    THEN pl.debit_amount - pl.credit_amount 
                    ELSE 0 
                END) as days_60_90,
                SUM(CASE 
                    WHEN CURRENT_DATE - pl.transaction_date > 90 
                    THEN pl.debit_amount - pl.credit_amount 
                    ELSE 0 
                END) as above_90
            FROM party_ledger pl
            WHERE pl.party_id = :party_id
            AND pl.debit_amount > pl.credit_amount
        """
        
        ageing = db.execute(
            text(ageing_query),
            {"party_id": party_id}
        ).first()
        
        return {
            "0-30": float(ageing.current_bucket or 0),
            "31-60": float(ageing.days_30_60 or 0),
            "61-90": float(ageing.days_60_90 or 0),
            "90+": float(ageing.above_90 or 0)
        }
        
    except Exception as e:
        logger.error(f"Error calculating ageing: {e}")
        return {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}

@router.get("/summary")
async def get_ledger_summary(
    party_type: Optional[str] = Query(None, description="customer/supplier/all"),
    db: Session = Depends(get_db)
):
    """
    Get summary of all party ledgers
    """
    try:
        base_query = """
            SELECT 
                COUNT(DISTINCT p.party_id) as total_parties,
                COUNT(DISTINCT CASE 
                    WHEN outstanding.balance > 0 THEN p.party_id 
                END) as parties_with_dues,
                COALESCE(SUM(CASE 
                    WHEN outstanding.balance > 0 THEN outstanding.balance 
                    ELSE 0 
                END), 0) as total_receivable,
                COALESCE(SUM(CASE 
                    WHEN outstanding.balance < 0 THEN ABS(outstanding.balance) 
                    ELSE 0 
                END), 0) as total_payable
            FROM parties p
            LEFT JOIN (
                SELECT 
                    party_id,
                    SUM(debit_amount) - SUM(credit_amount) as balance
                FROM party_ledger
                GROUP BY party_id
            ) outstanding ON p.party_id = outstanding.party_id
            WHERE 1=1
        """
        
        params = {}
        
        if party_type and party_type != "all":
            base_query += " AND p.party_type = :party_type"
            params["party_type"] = party_type
            
        summary = db.execute(text(base_query), params).first()
        
        # Get overdue summary
        overdue_query = """
            SELECT 
                COUNT(DISTINCT pl.party_id) as parties_overdue,
                COALESCE(SUM(pl.debit_amount - pl.credit_amount), 0) as amount_overdue
            FROM party_ledger pl
            JOIN parties p ON pl.party_id = p.party_id
            WHERE pl.due_date < CURRENT_DATE
            AND pl.debit_amount > pl.credit_amount
        """
        
        if party_type and party_type != "all":
            overdue_query += " AND p.party_type = :party_type"
            
        overdue = db.execute(text(overdue_query), params).first()
        
        return {
            "total_parties": summary.total_parties,
            "parties_with_dues": summary.parties_with_dues,
            "total_receivable": float(summary.total_receivable),
            "total_payable": float(summary.total_payable),
            "parties_overdue": overdue.parties_overdue,
            "amount_overdue": float(overdue.amount_overdue)
        }
        
    except Exception as e:
        logger.error(f"Error fetching ledger summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-reminder")
async def send_payment_reminder(
    reminder_data: dict,
    db: Session = Depends(get_db)
):
    """
    Send payment reminder to party via email/SMS
    """
    try:
        # Validate required fields
        if "party_id" not in reminder_data:
            raise HTTPException(status_code=400, detail="Party ID required")
            
        # Get party details
        party = db.execute(
            text("SELECT * FROM parties WHERE party_id = :party_id"),
            {"party_id": reminder_data["party_id"]}
        ).first()
        
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")
            
        # Get outstanding amount
        outstanding_query = """
            SELECT 
                COALESCE(SUM(debit_amount), 0) - COALESCE(SUM(credit_amount), 0) as balance
            FROM party_ledger
            WHERE party_id = :party_id
        """
        outstanding = db.execute(
            text(outstanding_query),
            {"party_id": reminder_data["party_id"]}
        ).scalar() or Decimal("0")
        
        if outstanding <= 0:
            raise HTTPException(
                status_code=400, 
                detail="No outstanding amount for this party"
            )
            
        # Log reminder sent
        db.execute(
            text("""
                INSERT INTO communication_log (
                    log_id, org_id, party_id, communication_type,
                    communication_date, subject, message, status
                ) VALUES (
                    gen_random_uuid(), :org_id, :party_id, :type,
                    CURRENT_TIMESTAMP, :subject, :message, 'sent'
                )
            """),
            {
                "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
                "party_id": reminder_data["party_id"],
                "type": reminder_data.get("reminder_type", "email"),
                "subject": f"Payment Reminder - Outstanding Amount: {outstanding}",
                "message": reminder_data.get("message", f"Your outstanding amount is {outstanding}")
            }
        )
        
        db.commit()
        
        # In real implementation, integrate with email/SMS service
        return {
            "status": "success",
            "message": f"Reminder sent to {party.party_name}",
            "outstanding_amount": float(outstanding),
            "reminder_type": reminder_data.get("reminder_type", "email")
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statement/{party_id}")
async def get_party_statement(
    party_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    format: str = Query("json", description="json/pdf"),
    db: Session = Depends(get_db)
):
    """
    Get party account statement
    """
    try:
        # Get ledger data
        ledger_data = await get_party_ledger(party_id, from_date, to_date, db)
        
        if format == "json":
            return ledger_data
        elif format == "pdf":
            # In real implementation, generate PDF
            return {
                "status": "success",
                "message": "PDF generation not implemented",
                "data": ledger_data
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating statement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconcile")
async def reconcile_ledger_entry(
    reconcile_data: dict,
    db: Session = Depends(get_db)
):
    """
    Reconcile ledger entries
    """
    try:
        # Validate required fields
        required_fields = ["ledger_id", "reconciled_date", "reconciled_by"]
        for field in required_fields:
            if field not in reconcile_data:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing required field: {field}"
                )
                
        # Update ledger entry
        db.execute(
            text("""
                UPDATE party_ledger
                SET reconciled = true,
                    reconciled_date = :reconciled_date,
                    reconciled_by = :reconciled_by,
                    reconciliation_notes = :notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE ledger_id = :ledger_id
            """),
            {
                "ledger_id": reconcile_data["ledger_id"],
                "reconciled_date": reconcile_data["reconciled_date"],
                "reconciled_by": reconcile_data["reconciled_by"],
                "notes": reconcile_data.get("notes", "")
            }
        )
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Ledger entry reconciled successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reconciling ledger: {e}")
        raise HTTPException(status_code=500, detail=str(e))