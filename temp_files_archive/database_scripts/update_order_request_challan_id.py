# Update to add challan_id and order_id support to OrderCreationRequest

# In api/services/enterprise_order_service.py, update OrderCreationRequest class:

class OrderCreationRequest(BaseModel):
    """Enterprise order creation request model with full validation"""
    # Customer Information
    customer_id: int = Field(..., gt=0)
    
    # Items (at least one required)
    items: List[OrderItemRequest] = Field(..., min_items=1)
    
    # Payment Information
    payment_mode: PaymentMode = PaymentMode.CASH
    payment_terms: Optional[str] = None
    payment_amount: Optional[Decimal] = Field(default=None, ge=0)
    
    # Order Details
    order_date: Optional[date] = None
    delivery_date: Optional[date] = None
    delivery_type: str = Field(default="pickup")  # pickup, delivery
    delivery_address: Optional[str] = None
    
    # Document References (NEW)
    order_id: Optional[int] = None  # Reference to existing order
    challan_id: Optional[int] = None  # Reference to existing challan
    
    # Amounts
    discount_amount: Decimal = Field(default=0, ge=0)
    delivery_charges: Decimal = Field(default=0, ge=0)
    other_charges: Decimal = Field(default=0, ge=0)
    
    # Metadata
    notes: Optional[str] = None
    reference_number: Optional[str] = None
    is_urgent: bool = False
    prescription_id: Optional[int] = None
    doctor_id: Optional[int] = None
    
    # Branch & User
    branch_id: Optional[int] = None
    created_by: Optional[int] = None

# In api/routers/v1/enterprise_orders.py, update _transform_quick_sale_request:

def _transform_quick_sale_request(request_data: dict) -> OrderCreationRequest:
    """Transform old quick-sale request format to enterprise format"""
    
    # Extract items and transform to new format
    items = []
    for item in request_data.get('items', []):
        enterprise_item = OrderItemRequest(
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item.get('unit_price'),
            discount_percent=item.get('discount_percent', 0),
            batch_id=item.get('batch_id')
        )
        items.append(enterprise_item)
    
    # Map payment mode
    payment_mode_map = {
        'cash': PaymentMode.CASH,
        'credit': PaymentMode.CREDIT,
        'card': PaymentMode.CARD,
        'upi': PaymentMode.UPI,
        'bank_transfer': PaymentMode.BANK_TRANSFER
    }
    
    payment_mode = payment_mode_map.get(
        request_data.get('payment_mode', 'cash').lower(), 
        PaymentMode.CASH
    )
    
    # Create enterprise request with document references
    return OrderCreationRequest(
        customer_id=request_data['customer_id'],
        items=items,
        payment_mode=payment_mode,
        payment_amount=request_data.get('payment_amount'),
        discount_amount=request_data.get('discount_amount', 0),
        delivery_charges=request_data.get('other_charges', 0),  # Map other_charges to delivery_charges
        notes=request_data.get('notes'),
        delivery_type="pickup",  # Default for quick-sale
        # Add document references (NEW)
        order_id=request_data.get('order_id'),
        challan_id=request_data.get('challan_id')
    )

# Also update the create_invoice method in EnterpriseOrderService to handle challan_id:

def _create_invoice(self, order_id: int, customer: CustomerInfo, 
                   order_items: List[ProcessedOrderItem], totals: Dict,
                   payment_mode: PaymentMode, payment_status: PaymentStatus,
                   notes: Optional[str], challan_id: Optional[int] = None) -> int:
    """Create invoice with all required fields properly populated"""
    
    invoice_number = self._generate_unique_invoice_number()
    
    # Prepare invoice data
    invoice_data = {
        'org_id': self.org_id,
        'invoice_number': invoice_number,
        'invoice_date': date.today(),
        'customer_id': customer.customer_id,
        'order_id': order_id,
        'challan_id': challan_id,  # NEW: Add challan reference
        'invoice_status': InvoiceStatus.GENERATED.value,
        'payment_status': payment_status.value,
        'payment_mode': payment_mode.value,
        # ... rest of the fields
    }
    
    # Insert invoice
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
    
    invoice_id = result.scalar()
    return invoice_id

# And update the create_order method to pass challan_id:

def create_order(self, request: OrderCreationRequest) -> OrderCreationResponse:
    """Create a complete order with invoice and payments"""
    try:
        # ... existing validation code ...
        
        # If challan_id is provided, validate it exists and hasn't been invoiced
        if request.challan_id:
            self._validate_challan_for_invoice(request.challan_id)
        
        # ... rest of the method ...
        
        # Step 7: Create invoice with challan reference
        invoice_id = self._create_invoice(
            order_id, customer, order_items, totals,
            request.payment_mode, payment_status, request.notes,
            request.challan_id  # Pass challan_id
        )
        
        # Step 8: If challan_id provided, mark it as converted
        if request.challan_id:
            self._mark_challan_as_converted(request.challan_id, invoice_id)
        
        # ... rest of the method ...

# Add validation and update methods:

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