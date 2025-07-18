"""
Payment management endpoints
Handles invoice payments, tracking, and reconciliation
"""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from ...database import get_db
from ...services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Default organization ID (should come from auth in production)
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"


class PaymentCreate(BaseModel):
    """Schema for recording a payment"""
    invoice_id: int
    payment_date: date = Field(default_factory=date.today)
    payment_mode: str = Field(..., pattern="^(cash|cheque|online|card|upi|neft|rtgs)$")
    amount: Decimal = Field(..., gt=0)
    transaction_reference: Optional[str] = None
    bank_name: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Schema for payment response"""
    payment_id: int
    payment_reference: str
    invoice_id: int
    amount: Decimal
    balance_amount: Decimal
    payment_status: str
    message: str


class PaymentListResponse(BaseModel):
    """Schema for payment list"""
    payments: List[dict]
    total: int


class PaymentSummaryResponse(BaseModel):
    """Schema for payment summary"""
    total_payments: int
    invoices_paid: int
    total_collected: Decimal
    payment_modes: dict
    pending: dict


@router.post("/record", response_model=PaymentResponse)
async def record_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Record a payment against an invoice
    
    - Validates payment amount against balance
    - Updates invoice payment status
    - Creates payment history record
    """
    try:
        result = PaymentService.record_payment(db, payment.invoice_id, payment.dict())
        db.commit()
        return PaymentResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to record payment: {str(e)}")


@router.get("/invoice/{invoice_id}", response_model=PaymentListResponse)
async def get_invoice_payments(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get all payments for a specific invoice"""
    try:
        payments = PaymentService.get_invoice_payments(db, invoice_id)
        return PaymentListResponse(payments=payments, total=len(payments))
    except Exception as e:
        logger.error(f"Error getting invoice payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payments")


@router.get("/summary", response_model=PaymentSummaryResponse)
async def get_payment_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get payment summary and analytics
    
    - Total collections by payment mode
    - Pending payment amounts
    - Payment trends
    """
    try:
        summary = PaymentService.get_payment_summary(
            db, DEFAULT_ORG_ID, from_date, to_date
        )
        return PaymentSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting payment summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment summary")


@router.put("/{payment_id}/cancel")
async def cancel_payment(
    payment_id: int,
    reason: str = Query(..., description="Cancellation reason"),
    db: Session = Depends(get_db)
):
    """
    Cancel a payment
    
    - Reverses the payment amount from invoice
    - Updates payment status to cancelled
    - Maintains audit trail
    """
    try:
        result = PaymentService.cancel_payment(db, payment_id, reason)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel payment")


@router.get("/outstanding")
async def get_outstanding_invoices(
    customer_id: Optional[int] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get list of outstanding invoices
    
    - Filter by customer
    - Option to show only overdue invoices
    - Includes aging analysis
    """
    try:
        query = """
            SELECT 
                i.invoice_id, i.invoice_number, i.invoice_date, i.due_date,
                c.customer_id, c.customer_name, c.customer_code,
                i.total_amount, i.paid_amount, 
                (i.total_amount - i.paid_amount) as balance_amount,
                i.payment_status,
                CASE 
                    WHEN i.due_date < CURRENT_DATE THEN 
                        CURRENT_DATE - i.due_date 
                    ELSE 0 
                END as days_overdue
            FROM invoices i
            JOIN customers c ON i.customer_id = c.customer_id
            JOIN orders o ON i.order_id = o.order_id
            WHERE o.org_id = :org_id
                AND i.payment_status IN ('unpaid', 'partial')
        """
        
        params = {"org_id": DEFAULT_ORG_ID}
        
        if customer_id:
            query += " AND c.customer_id = :customer_id"
            params["customer_id"] = customer_id
        
        if overdue_only:
            query += " AND i.due_date < CURRENT_DATE"
        
        query += " ORDER BY i.due_date, i.invoice_date"
        
        result = db.execute(query, params)
        invoices = [dict(row._mapping) for row in result]
        
        # Calculate summary
        total_outstanding = sum(inv["balance_amount"] for inv in invoices)
        total_overdue = sum(inv["balance_amount"] for inv in invoices if inv["days_overdue"] > 0)
        
        return {
            "invoices": invoices,
            "summary": {
                "total_invoices": len(invoices),
                "total_outstanding": total_outstanding,
                "total_overdue": total_overdue,
                "overdue_invoices": len([inv for inv in invoices if inv["days_overdue"] > 0])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting outstanding invoices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get outstanding invoices")