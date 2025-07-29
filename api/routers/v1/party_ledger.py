"""
Party Ledger API Router
Comprehensive ledger management for customers and suppliers
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from ...database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/party-ledger", tags=["party-ledger"])

@router.get("/balance/{party_id}")
async def get_party_balance(
    party_id: str,
    party_type: str = Query(..., regex="^(customer|supplier)$"),
    as_of_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get current balance for a party
    """
    try:
        query = """
            SELECT 
                COALESCE(SUM(debit_amount - credit_amount), 0) as balance,
                CASE 
                    WHEN COALESCE(SUM(debit_amount - credit_amount), 0) >= 0 THEN 'Dr'
                    ELSE 'Cr'
                END as balance_type,
                COUNT(*) as transaction_count,
                MAX(transaction_date) as last_transaction_date
            FROM party_ledger
            WHERE party_id = :party_id 
            AND party_type = :party_type
        """
        params = {"party_id": party_id, "party_type": party_type}
        
        if as_of_date:
            query += " AND transaction_date <= :as_of_date"
            params["as_of_date"] = as_of_date
            
        result = db.execute(text(query), params).fetchone()
        
        return {
            "party_id": party_id,
            "party_type": party_type,
            "balance": abs(float(result.balance)),
            "balance_type": result.balance_type if result.balance != 0 else "Dr",
            "transaction_count": result.transaction_count,
            "last_transaction_date": result.last_transaction_date,
            "as_of_date": as_of_date or date.today().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching party balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statement/{party_id}")
async def get_party_statement(
    party_id: str,
    party_type: str = Query(..., regex="^(customer|supplier)$"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get detailed statement for a party
    """
    try:
        # Base query
        query = """
            SELECT 
                ledger_id,
                transaction_date,
                transaction_type,
                reference_type,
                reference_id,
                reference_number,
                description,
                debit_amount,
                credit_amount,
                running_balance,
                balance_type,
                payment_mode,
                created_at
            FROM party_ledger
            WHERE party_id = :party_id
            AND party_type = :party_type
        """
        
        params = {
            "party_id": party_id,
            "party_type": party_type,
            "skip": skip,
            "limit": limit
        }
        
        # Add date filters
        if from_date:
            query += " AND transaction_date >= :from_date"
            params["from_date"] = from_date
        if to_date:
            query += " AND transaction_date <= :to_date"
            params["to_date"] = to_date
            
        # Order and pagination
        query += " ORDER BY transaction_date DESC, created_at DESC LIMIT :limit OFFSET :skip"
        
        # Get transactions
        transactions = db.execute(text(query), params).fetchall()
        
        # Get opening balance
        opening_query = """
            SELECT 
                COALESCE(SUM(debit_amount - credit_amount), 0) as opening_balance
            FROM party_ledger
            WHERE party_id = :party_id
            AND party_type = :party_type
        """
        opening_params = {"party_id": party_id, "party_type": party_type}
        
        if from_date:
            opening_query += " AND transaction_date < :from_date"
            opening_params["from_date"] = from_date
            
        opening_result = db.execute(text(opening_query), opening_params).fetchone()
        opening_balance = float(opening_result.opening_balance)
        
        # Format transactions
        statement_entries = []
        running_balance = opening_balance
        
        for txn in reversed(list(transactions)):  # Process in chronological order
            running_balance += float(txn.debit_amount) - float(txn.credit_amount)
            
            statement_entries.append({
                "ledger_id": txn.ledger_id,
                "date": txn.transaction_date,
                "transaction_type": txn.transaction_type,
                "reference": f"{txn.reference_type or ''} {txn.reference_number or ''}".strip(),
                "description": txn.description,
                "debit": float(txn.debit_amount) if txn.debit_amount > 0 else None,
                "credit": float(txn.credit_amount) if txn.credit_amount > 0 else None,
                "balance": abs(running_balance),
                "balance_type": "Dr" if running_balance >= 0 else "Cr",
                "payment_mode": txn.payment_mode
            })
            
        # Reverse to show latest first
        statement_entries.reverse()
        
        # Get party details
        if party_type == "customer":
            party_query = "SELECT customer_name as name, phone, email FROM customers WHERE customer_id = :party_id"
        else:
            party_query = "SELECT supplier_name as name, phone, email FROM suppliers WHERE supplier_id = :party_id"
            
        party = db.execute(text(party_query), {"party_id": party_id}).fetchone()
        
        return {
            "party_id": party_id,
            "party_name": party.name if party else "Unknown",
            "party_type": party_type,
            "phone": party.phone if party else None,
            "email": party.email if party else None,
            "from_date": from_date,
            "to_date": to_date,
            "opening_balance": abs(opening_balance),
            "opening_balance_type": "Dr" if opening_balance >= 0 else "Cr",
            "closing_balance": abs(running_balance),
            "closing_balance_type": "Dr" if running_balance >= 0 else "Cr",
            "transactions": statement_entries,
            "total_transactions": len(statement_entries)
        }
        
    except Exception as e:
        logger.error(f"Error fetching party statement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outstanding-bills/{party_id}")
async def get_outstanding_bills(
    party_id: str,
    party_type: str = Query(..., regex="^(customer|supplier)$"),
    status: Optional[str] = Query(None, regex="^(outstanding|partial|overdue|paid)$"),
    db: Session = Depends(get_db)
):
    """
    Get outstanding bills for a party
    """
    try:
        query = """
            SELECT 
                bill_id,
                bill_type,
                bill_number,
                bill_date,
                due_date,
                bill_amount,
                paid_amount,
                outstanding_amount,
                status,
                days_overdue,
                aging_bucket,
                reference_type,
                reference_id
            FROM outstanding_bills
            WHERE party_id = :party_id
            AND party_type = :party_type
        """
        params = {"party_id": party_id, "party_type": party_type}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        else:
            query += " AND status IN ('outstanding', 'partial', 'overdue')"
            
        query += " ORDER BY due_date, bill_date"
        
        bills = db.execute(text(query), params).fetchall()
        
        # Calculate summary
        summary = {
            "total_bills": len(bills),
            "total_outstanding": sum(float(bill.outstanding_amount) for bill in bills),
            "overdue_amount": sum(float(bill.outstanding_amount) for bill in bills if bill.days_overdue > 0),
            "current_amount": sum(float(bill.outstanding_amount) for bill in bills if bill.days_overdue <= 0)
        }
        
        # Format bills
        bills_data = []
        for bill in bills:
            bills_data.append({
                "bill_id": bill.bill_id,
                "bill_type": bill.bill_type,
                "bill_number": bill.bill_number,
                "bill_date": bill.bill_date,
                "due_date": bill.due_date,
                "bill_amount": float(bill.bill_amount),
                "paid_amount": float(bill.paid_amount),
                "outstanding_amount": float(bill.outstanding_amount),
                "status": bill.status,
                "days_overdue": bill.days_overdue,
                "aging_bucket": bill.aging_bucket,
                "reference": f"{bill.reference_type or ''} {bill.reference_id or ''}".strip()
            })
            
        return {
            "party_id": party_id,
            "party_type": party_type,
            "summary": summary,
            "bills": bills_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching outstanding bills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aging-analysis")
async def get_aging_analysis(
    party_type: Optional[str] = Query(None, regex="^(customer|supplier)$"),
    org_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get aging analysis for all parties or specific type
    """
    try:
        query = """
            SELECT 
                party_id,
                party_type,
                party_name,
                current_amount,
                overdue_0_30,
                overdue_31_60,
                overdue_61_90,
                overdue_91_120,
                overdue_above_120,
                total_outstanding,
                max_days_overdue
            FROM aging_analysis
            WHERE total_outstanding > 0
        """
        params = {}
        
        if party_type:
            query += " AND party_type = :party_type"
            params["party_type"] = party_type
            
        if org_id:
            query += " AND org_id = :org_id"
            params["org_id"] = org_id
            
        query += " ORDER BY total_outstanding DESC"
        
        results = db.execute(text(query), params).fetchall()
        
        # Calculate totals
        totals = {
            "current": 0,
            "0_30_days": 0,
            "31_60_days": 0,
            "61_90_days": 0,
            "91_120_days": 0,
            "above_120_days": 0,
            "total": 0
        }
        
        parties = []
        for row in results:
            totals["current"] += float(row.current_amount)
            totals["0_30_days"] += float(row.overdue_0_30)
            totals["31_60_days"] += float(row.overdue_31_60)
            totals["61_90_days"] += float(row.overdue_61_90)
            totals["91_120_days"] += float(row.overdue_91_120)
            totals["above_120_days"] += float(row.overdue_above_120)
            totals["total"] += float(row.total_outstanding)
            
            parties.append({
                "party_id": row.party_id,
                "party_type": row.party_type,
                "party_name": row.party_name,
                "aging": {
                    "current": float(row.current_amount),
                    "0_30_days": float(row.overdue_0_30),
                    "31_60_days": float(row.overdue_31_60),
                    "61_90_days": float(row.overdue_61_90),
                    "91_120_days": float(row.overdue_91_120),
                    "above_120_days": float(row.overdue_above_120)
                },
                "total_outstanding": float(row.total_outstanding),
                "max_days_overdue": row.max_days_overdue
            })
            
        return {
            "summary": totals,
            "party_count": len(parties),
            "parties": parties
        }
        
    except Exception as e:
        logger.error(f"Error fetching aging analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entry")
async def create_ledger_entry(
    entry_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new ledger entry
    """
    try:
        # Validate required fields
        required_fields = ["party_id", "party_type", "transaction_date", "transaction_type"]
        for field in required_fields:
            if field not in entry_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
                
        # Ensure either debit or credit amount is provided
        if not entry_data.get("debit_amount") and not entry_data.get("credit_amount"):
            raise HTTPException(status_code=400, detail="Either debit_amount or credit_amount must be provided")
            
        # Insert ledger entry
        result = db.execute(
            text("""
                INSERT INTO party_ledger (
                    org_id, party_id, party_type,
                    transaction_date, transaction_type,
                    reference_type, reference_id, reference_number,
                    debit_amount, credit_amount,
                    description, narration,
                    payment_mode, instrument_number,
                    instrument_date, bank_name
                ) VALUES (
                    :org_id, :party_id, :party_type,
                    :transaction_date, :transaction_type,
                    :reference_type, :reference_id, :reference_number,
                    :debit_amount, :credit_amount,
                    :description, :narration,
                    :payment_mode, :instrument_number,
                    :instrument_date, :bank_name
                )
                RETURNING ledger_id, running_balance, balance_type
            """),
            {
                "org_id": entry_data.get("org_id", "12de5e22-eee7-4d25-b3a7-d16d01c6170f"),
                "party_id": entry_data["party_id"],
                "party_type": entry_data["party_type"],
                "transaction_date": entry_data["transaction_date"],
                "transaction_type": entry_data["transaction_type"],
                "reference_type": entry_data.get("reference_type"),
                "reference_id": entry_data.get("reference_id"),
                "reference_number": entry_data.get("reference_number"),
                "debit_amount": Decimal(str(entry_data.get("debit_amount", 0))),
                "credit_amount": Decimal(str(entry_data.get("credit_amount", 0))),
                "description": entry_data.get("description"),
                "narration": entry_data.get("narration"),
                "payment_mode": entry_data.get("payment_mode"),
                "instrument_number": entry_data.get("instrument_number"),
                "instrument_date": entry_data.get("instrument_date"),
                "bank_name": entry_data.get("bank_name")
            }
        ).fetchone()
        
        # Handle bill creation/update if it's an invoice or payment
        if entry_data["transaction_type"] == "invoice":
            # Create outstanding bill
            db.execute(
                text("""
                    INSERT INTO outstanding_bills (
                        org_id, party_id, party_type,
                        bill_type, bill_number, bill_date,
                        due_date, reference_type, reference_id,
                        bill_amount
                    ) VALUES (
                        :org_id, :party_id, :party_type,
                        :bill_type, :bill_number, :bill_date,
                        :due_date, :reference_type, :reference_id,
                        :bill_amount
                    )
                    ON CONFLICT (org_id, bill_number) DO NOTHING
                """),
                {
                    "org_id": entry_data.get("org_id", "12de5e22-eee7-4d25-b3a7-d16d01c6170f"),
                    "party_id": entry_data["party_id"],
                    "party_type": entry_data["party_type"],
                    "bill_type": "invoice" if entry_data["party_type"] == "customer" else "purchase_bill",
                    "bill_number": entry_data.get("reference_number"),
                    "bill_date": entry_data["transaction_date"],
                    "due_date": entry_data.get("due_date", 
                        (datetime.strptime(entry_data["transaction_date"], "%Y-%m-%d") + timedelta(days=30)).date()
                    ),
                    "reference_type": entry_data.get("reference_type"),
                    "reference_id": entry_data.get("reference_id"),
                    "bill_amount": Decimal(str(entry_data.get("debit_amount", 0)))
                }
            )
            
        elif entry_data["transaction_type"] == "payment":
            # Allocate payment to outstanding bills (FIFO)
            payment_amount = Decimal(str(entry_data.get("credit_amount", 0)))
            if payment_amount > 0:
                _allocate_payment_to_bills(
                    db, 
                    entry_data["party_id"], 
                    entry_data["party_type"],
                    payment_amount,
                    result.ledger_id
                )
        
        db.commit()
        
        return {
            "status": "success",
            "ledger_id": result.ledger_id,
            "running_balance": float(result.running_balance),
            "balance_type": result.balance_type,
            "message": "Ledger entry created successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ledger entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconcile/{ledger_id}")
async def reconcile_entry(
    ledger_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark a ledger entry as reconciled
    """
    try:
        result = db.execute(
            text("""
                UPDATE party_ledger
                SET is_reconciled = TRUE,
                    reconciliation_date = CURRENT_DATE
                WHERE ledger_id = :ledger_id
                RETURNING ledger_id
            """),
            {"ledger_id": ledger_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Ledger entry not found")
            
        db.commit()
        
        return {
            "status": "success",
            "message": "Entry reconciled successfully"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reconciling entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _allocate_payment_to_bills(
    db: Session, 
    party_id: str, 
    party_type: str,
    payment_amount: Decimal,
    payment_ledger_id: str
):
    """
    Internal function to allocate payment to outstanding bills using FIFO
    """
    # Get outstanding bills in FIFO order
    bills = db.execute(
        text("""
            SELECT bill_id, outstanding_amount
            FROM outstanding_bills
            WHERE party_id = :party_id
            AND party_type = :party_type
            AND status IN ('outstanding', 'partial', 'overdue')
            ORDER BY bill_date, bill_id
            FOR UPDATE
        """),
        {"party_id": party_id, "party_type": party_type}
    ).fetchall()
    
    remaining_amount = payment_amount
    
    for bill in bills:
        if remaining_amount <= 0:
            break
            
        allocation_amount = min(remaining_amount, Decimal(str(bill.outstanding_amount)))
        
        # Create allocation record
        db.execute(
            text("""
                INSERT INTO payment_allocations (
                    payment_ledger_id, bill_id,
                    allocated_amount, allocation_date
                ) VALUES (
                    :payment_ledger_id, :bill_id,
                    :allocated_amount, CURRENT_DATE
                )
            """),
            {
                "payment_ledger_id": payment_ledger_id,
                "bill_id": bill.bill_id,
                "allocated_amount": allocation_amount
            }
        )
        
        # Update bill
        db.execute(
            text("""
                UPDATE outstanding_bills
                SET paid_amount = paid_amount + :amount
                WHERE bill_id = :bill_id
            """),
            {
                "amount": allocation_amount,
                "bill_id": bill.bill_id
            }
        )
        
        remaining_amount -= allocation_amount

@router.get("/reminders/pending")
async def get_pending_reminders(
    reminder_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get pending collection reminders
    """
    try:
        query = """
            SELECT 
                r.reminder_id,
                r.party_id,
                r.reminder_type,
                r.reminder_date,
                r.message_content,
                r.outstanding_amount,
                r.bills_count,
                c.customer_name as party_name,
                c.phone,
                c.email
            FROM collection_reminders r
            JOIN customers c ON r.party_id = c.customer_id
            WHERE r.status = 'pending'
        """
        params = {}
        
        if reminder_date:
            query += " AND r.reminder_date = :reminder_date"
            params["reminder_date"] = reminder_date
        else:
            query += " AND r.reminder_date <= CURRENT_DATE"
            
        query += " ORDER BY r.reminder_date, r.created_at"
        
        reminders = db.execute(text(query), params).fetchall()
        
        return {
            "count": len(reminders),
            "reminders": [
                {
                    "reminder_id": r.reminder_id,
                    "party_id": r.party_id,
                    "party_name": r.party_name,
                    "phone": r.phone,
                    "email": r.email,
                    "reminder_type": r.reminder_type,
                    "reminder_date": r.reminder_date,
                    "message": r.message_content,
                    "outstanding_amount": float(r.outstanding_amount) if r.outstanding_amount else 0,
                    "bills_count": r.bills_count
                }
                for r in reminders
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))