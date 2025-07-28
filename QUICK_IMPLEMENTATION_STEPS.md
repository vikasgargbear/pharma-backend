# Quick Implementation Steps for challan_id Support

## Files to Modify

### 1. `/api/services/enterprise_order_service.py`

**Line ~150** - In `OrderCreationRequest` class, add:
```python
# Document References (NEW)
order_id: Optional[int] = None  # Reference to existing order
challan_id: Optional[int] = None  # Reference to existing challan
```

**Add these methods to `EnterpriseOrderService` class:**
```python
def _validate_challan_for_invoice(self, challan_id: int):
    """Validate challan exists and hasn't been converted to invoice"""
    result = self.db.execute(
        text("""
            SELECT challan_id, converted_to_invoice, customer_id, challan_number
            FROM challans
            WHERE challan_id = :challan_id AND org_id = :org_id
        """),
        {"challan_id": challan_id, "org_id": self.org_id}
    ).fetchone()
    
    if not result:
        raise OrderServiceError(f"Challan {challan_id} not found", "CHALLAN_NOT_FOUND")
    
    if result.converted_to_invoice:
        raise OrderServiceError(
            f"Challan {result.challan_number} has already been converted to invoice",
            "CHALLAN_ALREADY_CONVERTED"
        )
    
    return result

def _mark_challan_as_converted(self, challan_id: int, invoice_id: int):
    """Mark challan as converted to invoice"""
    self.db.execute(
        text("""
            UPDATE challans
            SET converted_to_invoice = TRUE,
                invoice_id = :invoice_id,
                conversion_date = CURRENT_TIMESTAMP
            WHERE challan_id = :challan_id AND org_id = :org_id
        """),
        {"challan_id": challan_id, "invoice_id": invoice_id, "org_id": self.org_id}
    )
```

**In `create_order` method, after customer validation add:**
```python
# If challan_id is provided, validate it exists and hasn't been invoiced
if request.challan_id:
    self._validate_challan_for_invoice(request.challan_id)
```

**Update `_create_invoice` method signature:**
```python
def _create_invoice(self, order_id: int, customer: CustomerInfo, 
                   order_items: List[ProcessedOrderItem], totals: Dict,
                   payment_mode: PaymentMode, payment_status: PaymentStatus,
                   notes: Optional[str], challan_id: Optional[int] = None) -> int:
```

**In `_create_invoice`, add challan_id to invoice_data:**
```python
'challan_id': challan_id,  # NEW: Add challan reference
```

**Update the INSERT statement in `_create_invoice` to include `challan_id` in both columns and values**

**Where `_create_invoice` is called, update to:**
```python
invoice_id = self._create_invoice(
    order_id, customer, order_items, totals,
    request.payment_mode, payment_status, request.notes,
    request.challan_id  # Pass challan_id
)

# If challan_id provided, mark it as converted
if request.challan_id:
    self._mark_challan_as_converted(request.challan_id, invoice_id)
```

### 2. `/api/routers/v1/enterprise_orders.py`

**In `_transform_quick_sale_request` function (~line 170), add before return:**
```python
# Add document references (NEW)
order_id=request_data.get('order_id'),
challan_id=request_data.get('challan_id')
```

### 3. `/api/routers/v1/invoices.py`

**Add this new endpoint:**
```python
@router.post("/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: int,
    payment_data: dict,
    db: Session = Depends(get_db),
    current_org = Depends(get_current_org)
):
    """Record payment for an invoice"""
    try:
        org_id = current_org["org_id"]
        
        # Verify invoice exists
        invoice = db.execute(
            text("""
                SELECT invoice_id, total_amount, payment_status, 
                       COALESCE(amount_paid, 0) as amount_paid
                FROM invoices
                WHERE invoice_id = :invoice_id AND org_id = :org_id
            """),
            {"invoice_id": invoice_id, "org_id": org_id}
        ).fetchone()
        
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        
        # Validate payment amount
        remaining = invoice.total_amount - invoice.amount_paid
        if payment_data['amount'] > remaining:
            raise HTTPException(400, f"Payment exceeds remaining balance of {remaining}")
        
        # Record payment
        result = db.execute(
            text("""
                INSERT INTO invoice_payments (
                    invoice_id, payment_date, payment_mode, amount,
                    transaction_id, bank_name, cheque_number, notes,
                    created_at, created_by
                ) VALUES (
                    :invoice_id, :payment_date, :payment_mode, :amount,
                    :transaction_id, :bank_name, :cheque_number, :notes,
                    CURRENT_TIMESTAMP, :created_by
                ) RETURNING payment_id
            """),
            {
                "invoice_id": invoice_id,
                "payment_date": payment_data.get('payment_date', date.today()),
                "payment_mode": payment_data['payment_mode'],
                "amount": payment_data['amount'],
                "transaction_id": payment_data.get('transaction_id'),
                "bank_name": payment_data.get('bank_name'),
                "cheque_number": payment_data.get('cheque_number'),
                "notes": payment_data.get('notes'),
                "created_by": 1
            }
        )
        
        payment_id = result.scalar()
        
        # Update invoice payment status
        new_amount_paid = invoice.amount_paid + payment_data['amount']
        payment_status = 'paid' if new_amount_paid >= invoice.total_amount else 'partial'
        
        db.execute(
            text("""
                UPDATE invoices
                SET amount_paid = :amount_paid,
                    payment_status = :payment_status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE invoice_id = :invoice_id
            """),
            {
                "amount_paid": new_amount_paid,
                "payment_status": payment_status,
                "invoice_id": invoice_id
            }
        )
        
        db.commit()
        
        return {
            "payment_id": payment_id,
            "invoice_id": invoice_id,
            "amount_paid": new_amount_paid,
            "payment_status": payment_status,
            "message": "Payment recorded successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to record payment: {str(e)}")
```

## Testing

After making these changes:

1. Restart your FastAPI server
2. Test creating an invoice from a challan
3. Test payment recording
4. Verify the challan is marked as converted

That's it! The backend will now support creating invoices from challans and recording payments.