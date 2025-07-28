# Implementation Guide: Adding challan_id Support to Invoice Creation

## Overview
This guide provides step-by-step instructions to implement challan_id support in the backend, allowing invoices to be created from challans without requiring an order.

## Step 1: Database Changes (Already Completed)
✅ You've already run the SQL script `add_challan_id_to_invoices.sql`

## Step 2: Update the OrderCreationRequest Model

### File: `/api/services/enterprise_order_service.py`

1. Find the `OrderCreationRequest` class (around line 130-177)
2. Add these two fields after the delivery_address field:

```python
# Document References (NEW)
order_id: Optional[int] = None  # Reference to existing order
challan_id: Optional[int] = None  # Reference to existing challan
```

## Step 3: Update the Quick-Sale Transform Function

### File: `/api/routers/v1/enterprise_orders.py`

1. Find the `_transform_quick_sale_request` function (around line 139)
2. Add these lines before the return statement:

```python
# Add document references (NEW)
order_id=request_data.get('order_id'),
challan_id=request_data.get('challan_id')
```

## Step 4: Add Challan Validation Methods

### File: `/api/services/enterprise_order_service.py`

Add these new methods to the `EnterpriseOrderService` class:

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
        raise OrderServiceError(
            f"Challan {challan_id} not found",
            "CHALLAN_NOT_FOUND"
        )
    
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
        {
            "challan_id": challan_id,
            "invoice_id": invoice_id,
            "org_id": self.org_id
        }
    )
```

## Step 5: Update create_order Method

### File: `/api/services/enterprise_order_service.py`

In the `create_order` method, add challan validation after customer validation:

```python
# After customer validation (around line 231)
# If challan_id is provided, validate it exists and hasn't been invoiced
if request.challan_id:
    self._validate_challan_for_invoice(request.challan_id)
```

## Step 6: Update _create_invoice Method

### File: `/api/services/enterprise_order_service.py`

1. Update the method signature to accept challan_id:

```python
def _create_invoice(self, order_id: int, customer: CustomerInfo, 
                   order_items: List[ProcessedOrderItem], totals: Dict,
                   payment_mode: PaymentMode, payment_status: PaymentStatus,
                   notes: Optional[str], challan_id: Optional[int] = None) -> int:
```

2. Add challan_id to the invoice_data dictionary:

```python
invoice_data = {
    'org_id': self.org_id,
    'invoice_number': invoice_number,
    'invoice_date': date.today(),
    'customer_id': customer.customer_id,
    'order_id': order_id,
    'challan_id': challan_id,  # NEW: Add challan reference
    # ... rest of the fields
}
```

3. Update the INSERT statement to include challan_id:

```python
result = self.db.execute(
    text("""
        INSERT INTO invoices (
            org_id, invoice_number, invoice_date, customer_id, order_id, challan_id,
            invoice_status, payment_status, payment_mode,
            subtotal_amount, discount_amount, tax_amount, final_amount,
            cgst_amount, sgst_amount, igst_amount, other_charges,
            round_off, notes, created_at, created_by
        ) VALUES (
            :org_id, :invoice_number, :invoice_date, :customer_id, :order_id, :challan_id,
            :invoice_status, :payment_status, :payment_mode,
            :subtotal_amount, :discount_amount, :tax_amount, :final_amount,
            :cgst_amount, :sgst_amount, :igst_amount, :other_charges,
            :round_off, :notes, CURRENT_TIMESTAMP, :created_by
        ) RETURNING invoice_id
    """),
    invoice_data
)
```

## Step 7: Update create_order to Pass challan_id

### File: `/api/services/enterprise_order_service.py`

1. Find where `_create_invoice` is called in the `create_order` method
2. Update the call to pass challan_id:

```python
# Step 7: Create invoice with challan reference
invoice_id = self._create_invoice(
    order_id, customer, order_items, totals,
    request.payment_mode, payment_status, request.notes,
    request.challan_id  # Pass challan_id
)

# Step 8: If challan_id provided, mark it as converted
if request.challan_id:
    self._mark_challan_as_converted(request.challan_id, invoice_id)
```

## Step 8: Update Challan to Invoice Converter

### File: `/api/routers/v1/challan_to_invoice.py`

The challan-to-invoice endpoint should already work correctly, but verify it updates the new tracking fields when creating invoices from challans.

## Step 9: Add Payment Recording Endpoint

### File: `/api/routers/v1/invoices.py`

Add this endpoint to handle payment recording:

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
        
        # Verify invoice exists and get current payment status
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
            raise HTTPException(400, f"Payment amount exceeds remaining balance of {remaining}")
        
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
                "created_by": payment_data.get('created_by', 1)
            }
        )
        
        payment_id = result.scalar()
        
        # Update invoice payment status
        new_amount_paid = invoice.amount_paid + payment_data['amount']
        if new_amount_paid >= invoice.total_amount:
            payment_status = 'paid'
        else:
            payment_status = 'partial'
        
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
        logger.error(f"Error recording payment: {str(e)}")
        raise HTTPException(500, f"Failed to record payment: {str(e)}")
```

## Step 10: Test the Implementation

1. **Test creating invoice with challan_id**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/enterprise-orders/quick-sale \
     -H "Content-Type: application/json" \
     -d '{
       "customer_id": 1,
       "challan_id": 123,
       "items": [...],
       "payment_mode": "cash"
     }'
   ```

2. **Test challan validation**:
   - Try creating invoice from non-existent challan
   - Try creating invoice from already-converted challan

3. **Test payment recording**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/invoices/1/record-payment \
     -H "Content-Type: application/json" \
     -d '{
       "payment_mode": "cash",
       "amount": 1000,
       "payment_date": "2024-07-27"
     }'
   ```

## Summary

After implementing these changes:
1. ✅ Invoices can be created with reference to challans
2. ✅ Challans are tracked when converted to invoices
3. ✅ Frontend can pass challan_id when creating invoices
4. ✅ Payment recording is available for invoices
5. ✅ Document linking is properly maintained

The system now supports flexible document flows:
- Direct Invoice (no order/challan)
- Order → Invoice
- Challan → Invoice
- Order → Challan → Invoice