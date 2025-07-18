"""
Business Logic Module for Pharma E-commerce System
Handles real-time inventory updates, payment processing, and automatic triggers
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date
from typing import List, Dict
import json

try:
    from . import models, schemas
except ImportError:
    import models
    import schemas

class InventoryManager:
    """Handles real-time inventory updates and FIFO logic"""
    
    @staticmethod
    def process_order_inventory(db: Session, order_items: List[schemas.OrderItemCreate], user_id: int = None):
        """
        Process inventory changes when an order is placed
        Implements FIFO (First In, First Out) logic for batch selection
        """
        inventory_transactions = []
        
        for item in order_items:
            # Get the batch
            batch = db.query(models.Batch).filter(models.Batch.batch_id == item.batch_id).first()
            if not batch:
                raise ValueError(f"Batch {item.batch_id} not found")
            
            # Check if sufficient quantity available
            current_status = InventoryManager.get_batch_status(db, item.batch_id)
            if current_status.available_quantity < item.quantity:
                raise ValueError(f"Insufficient inventory for batch {batch.batch_number}. Available: {current_status.available_quantity}, Required: {item.quantity}")
            
            # Create inventory transaction record
            quantity_before = current_status.current_quantity
            quantity_after = quantity_before - item.quantity
            
            inventory_transaction = models.InventoryTransaction(
                batch_id=item.batch_id,
                transaction_type='sale',
                quantity_change=-item.quantity,  # Negative for outbound
                reference_type='order_item',
                reference_id=item.order_item_id if hasattr(item, 'order_item_id') else None,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                performed_by=user_id,
                remarks=f"Order sale - {item.quantity} units",
                is_automatic=True
            )
            
            db.add(inventory_transaction)
            inventory_transactions.append(inventory_transaction)
            
            # Update batch inventory status
            InventoryManager.update_batch_status(db, item.batch_id)
            
            # Create inventory movement record for backward compatibility
            inventory_movement = models.InventoryMovement(
                batch_id=item.batch_id,
                movement_type='out',
                quantity=item.quantity,
                reference=f"Order Item Sale"
            )
            db.add(inventory_movement)
        
        db.commit()
        return inventory_transactions
    
    @staticmethod
    def process_purchase_inventory(db: Session, purchase_items: List[Dict], user_id: int = None):
        """Process inventory changes when a purchase is received"""
        inventory_transactions = []
        
        for item in purchase_items:
            batch_id = item['batch_id']
            quantity = item['quantity']
            
            # Get current status
            current_status = InventoryManager.get_batch_status(db, batch_id)
            quantity_before = current_status.current_quantity
            quantity_after = quantity_before + quantity
            
            # Create inventory transaction
            inventory_transaction = models.InventoryTransaction(
                batch_id=batch_id,
                transaction_type='purchase',
                quantity_change=quantity,  # Positive for inbound
                reference_type='purchase_item',
                reference_id=item.get('purchase_item_id'),
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                performed_by=user_id,
                remarks=f"Purchase received - {quantity} units",
                is_automatic=True
            )
            
            db.add(inventory_transaction)
            inventory_transactions.append(inventory_transaction)
            
            # Update batch inventory status
            InventoryManager.update_batch_status(db, batch_id)
            
            # Create inventory movement record
            inventory_movement = models.InventoryMovement(
                batch_id=batch_id,
                movement_type='in',
                quantity=quantity,
                reference=f"Purchase Receipt"
            )
            db.add(inventory_movement)
        
        db.commit()
        return inventory_transactions
    
    @staticmethod
    def get_batch_status(db: Session, batch_id: int) -> models.BatchInventoryStatus:
        """Get or create batch inventory status"""
        status = db.query(models.BatchInventoryStatus).filter(
            models.BatchInventoryStatus.batch_id == batch_id
        ).first()
        
        if not status:
            # Initialize status if not exists
            batch = db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()
            status = models.BatchInventoryStatus(
                batch_id=batch_id,
                current_quantity=batch.quantity if batch else 0,
                available_quantity=batch.quantity if batch else 0
            )
            db.add(status)
            db.commit()
            db.refresh(status)
        
        return status
    
    @staticmethod
    def update_batch_status(db: Session, batch_id: int):
        """Update batch inventory status based on transactions"""
        # Calculate current quantity from all transactions
        total_change = db.query(func.sum(models.InventoryTransaction.quantity_change)).filter(
            models.InventoryTransaction.batch_id == batch_id
        ).scalar() or 0
        
        # Get initial batch quantity
        batch = db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()
        initial_quantity = batch.quantity if batch else 0
        
        current_quantity = initial_quantity + total_change
        
        # Calculate reserved quantity (pending orders)
        reserved_quantity = db.query(func.sum(models.OrderItem.quantity)).join(
            models.Order
        ).filter(
            and_(
                models.OrderItem.batch_id == batch_id,
                models.Order.status.in_(['placed', 'confirmed', 'processing'])
            )
        ).scalar() or 0
        
        available_quantity = max(0, current_quantity - reserved_quantity)
        
        # Update or create status
        status = InventoryManager.get_batch_status(db, batch_id)
        status.current_quantity = current_quantity
        status.reserved_quantity = reserved_quantity
        status.available_quantity = available_quantity
        
        # Update status flags
        status.is_out_of_stock = current_quantity <= 0
        status.is_low_stock = current_quantity <= status.minimum_stock_level
        status.needs_reorder = current_quantity <= status.reorder_level
        status.last_updated = datetime.utcnow()
        
        db.commit()
        
    @staticmethod
    def get_fifo_batches(db: Session, product_id: int, required_quantity: int) -> List[Dict]:
        """
        FIXED: Get FIFO batch RECOMMENDATIONS (not automatic selection)
        Frontend should use this for batch suggestions, then user selects specific batches
        """
        # Get available batches sorted by expiry date (FIFO recommendations)
        available_batches = db.query(
            models.Batch,
            models.BatchInventoryStatus.available_quantity
        ).join(
            models.BatchInventoryStatus,
            models.Batch.batch_id == models.BatchInventoryStatus.batch_id
        ).filter(
            and_(
                models.Batch.product_id == product_id,
                models.BatchInventoryStatus.available_quantity > 0,
                models.Batch.expiry_date > date.today()  # Only non-expired batches
            )
        ).order_by(models.Batch.expiry_date.asc()).all()
        
        recommendations = []
        remaining_quantity = required_quantity
        
        for batch, available_qty in available_batches:
            quantity_to_recommend = min(remaining_quantity, available_qty)
            recommendations.append({
                'batch_id': batch.batch_id,
                'batch_number': batch.batch_number,
                'recommended_quantity': quantity_to_recommend,
                'available_quantity': available_qty,
                'expiry_date': batch.expiry_date,
                'purchase_price': batch.purchase_price,
                'sale_price': batch.sale_price,
                'recommendation_reason': 'FIFO - Earliest expiry first'
            })
            remaining_quantity -= quantity_to_recommend
            
            if remaining_quantity <= 0:
                break
        
        return {
            'product_id': product_id,
            'requested_quantity': required_quantity,
            'total_available': sum(batch[1] for batch in available_batches),
            'can_fulfill': remaining_quantity <= 0,
            'shortage': max(0, remaining_quantity),
            'recommendations': recommendations
        }

    @staticmethod
    def process_sales_return(db: Session, return_items: List[Dict], user_id: int = None):
        """
        MISSING: Process inventory and financial updates when sales return is processed
        """
        inventory_transactions = []
        
        for item in return_items:
            batch_id = item['batch_id']
            return_quantity = item['return_quantity']
            
            # Get current status
            current_status = InventoryManager.get_batch_status(db, batch_id)
            quantity_before = current_status.current_quantity
            quantity_after = quantity_before + return_quantity  # Add back to inventory
            
            # Create inventory transaction
            inventory_transaction = models.InventoryTransaction(
                batch_id=batch_id,
                transaction_type='return',
                quantity_change=return_quantity,  # Positive for return
                reference_type='sales_return_item',
                reference_id=item.get('return_item_id'),
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                performed_by=user_id,
                remarks=f"Sales return - {return_quantity} units returned",
                is_automatic=True
            )
            
            db.add(inventory_transaction)
            inventory_transactions.append(inventory_transaction)
            
            # Update batch inventory status
            InventoryManager.update_batch_status(db, batch_id)
        
        db.commit()
        return inventory_transactions

    @staticmethod
    def process_stock_adjustment(db: Session, adjustments: List[Dict], reason: str, user_id: int = None):
        """
        MISSING: Process manual stock adjustments with audit trail
        """
        inventory_transactions = []
        
        for adjustment in adjustments:
            batch_id = adjustment['batch_id']
            adjustment_quantity = adjustment['adjustment_quantity']  # Can be positive or negative
            
            # Get current status
            current_status = InventoryManager.get_batch_status(db, batch_id)
            quantity_before = current_status.current_quantity
            quantity_after = quantity_before + adjustment_quantity
            
            # Create inventory transaction
            inventory_transaction = models.InventoryTransaction(
                batch_id=batch_id,
                transaction_type='adjustment',
                quantity_change=adjustment_quantity,
                reference_type='manual_adjustment',
                reference_id=None,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                performed_by=user_id,
                remarks=f"Stock adjustment: {reason}",
                is_automatic=False  # Manual adjustment
            )
            
            db.add(inventory_transaction)
            inventory_transactions.append(inventory_transaction)
            
            # Update batch inventory status
            InventoryManager.update_batch_status(db, batch_id)
        
        db.commit()
        return inventory_transactions

    @staticmethod
    def process_expiry_management(db: Session, days_ahead: int = 30):
        """
        MISSING: Automatic expiry management and alerts
        """
        from datetime import timedelta
        expiry_threshold = date.today() + timedelta(days=days_ahead)
        
        # Find batches expiring soon
        expiring_batches = db.query(models.Batch).join(
            models.BatchInventoryStatus
        ).filter(
            and_(
                models.Batch.expiry_date <= expiry_threshold,
                models.BatchInventoryStatus.current_quantity > 0
            )
        ).all()
        
        alerts = []
        for batch in expiring_batches:
            days_to_expiry = (batch.expiry_date - date.today()).days
            
            if days_to_expiry <= 0:
                # Already expired - mark as such
                status = InventoryManager.get_batch_status(db, batch.batch_id)
                status.is_out_of_stock = True  # Treat expired as out of stock
                alert_type = 'EXPIRED'
            elif days_to_expiry <= 7:
                alert_type = 'CRITICAL_EXPIRY'
            elif days_to_expiry <= 30:
                alert_type = 'WARNING_EXPIRY'
            else:
                continue
            
            alerts.append({
                'batch_id': batch.batch_id,
                'batch_number': batch.batch_number,
                'product_id': batch.product_id,
                'expiry_date': batch.expiry_date,
                'days_to_expiry': days_to_expiry,
                'current_quantity': status.current_quantity,
                'alert_type': alert_type
            })
        
        db.commit()
        return alerts

class PaymentManager:
    """Handles complex payment scenarios and allocations"""
    
    @staticmethod
    def create_payment_with_allocation(
        db: Session,
        customer_id: int,
        amount: float,
        payment_mode: str,
        order_ids: List[int] = None,
        payment_type: str = 'order_payment',
        **kwargs
    ) -> models.Payment:
        """
        Create a payment and automatically allocate to orders
        Supports partial payments, multi-order payments, and advance payments
        """
        # Create the payment
        payment = models.Payment(
            customer_id=customer_id,
            amount=amount,
            payment_mode=payment_mode,
            payment_type=payment_type,
            **kwargs
        )
        db.add(payment)
        db.flush()  # Get payment_id
        
        remaining_amount = amount
        
        if payment_type == 'advance' or not order_ids:
            # Handle advance payment
            advance_payment = models.CustomerAdvancePayment(
                customer_id=customer_id,
                payment_id=payment.payment_id,
                advance_amount=amount,
                remaining_amount=amount
            )
            db.add(advance_payment)
        else:
            # Allocate to specific orders
            for order_id in order_ids:
                if remaining_amount <= 0:
                    break
                
                # Get order outstanding amount
                order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
                if not order:
                    continue
                
                # Calculate how much is already paid for this order
                already_paid = db.query(func.sum(models.PaymentAllocation.allocated_amount)).filter(
                    models.PaymentAllocation.order_id == order_id
                ).scalar() or 0
                
                outstanding = order.final_amount - already_paid
                allocation_amount = min(remaining_amount, outstanding)
                
                if allocation_amount > 0:
                    # Create payment allocation
                    allocation = models.PaymentAllocation(
                        payment_id=payment.payment_id,
                        order_id=order_id,
                        allocated_amount=allocation_amount,
                        remarks=f"Payment allocation for order {order_id}"
                    )
                    db.add(allocation)
                    remaining_amount -= allocation_amount
                    
                    # Update order payment status
                    PaymentManager.update_order_payment_status(db, order_id)
            
            # If there's remaining amount, treat as advance
            if remaining_amount > 0:
                advance_payment = models.CustomerAdvancePayment(
                    customer_id=customer_id,
                    payment_id=payment.payment_id,
                    advance_amount=remaining_amount,
                    remaining_amount=remaining_amount
                )
                db.add(advance_payment)
        
        db.commit()
        return payment
    
    @staticmethod
    def update_order_payment_status(db: Session, order_id: int):
        """Update order payment status based on allocations"""
        order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
        if not order:
            return
        
        total_paid = db.query(func.sum(models.PaymentAllocation.allocated_amount)).filter(
            models.PaymentAllocation.order_id == order_id
        ).scalar() or 0
        
        if total_paid >= order.final_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partial'
        else:
            order.payment_status = 'pending'
        
        db.commit()
    
    @staticmethod
    def apply_advance_payment(db: Session, customer_id: int, order_id: int, amount: float):
        """Apply advance payment to an order"""
        # Find available advance payments
        advance_payments = db.query(models.CustomerAdvancePayment).filter(
            and_(
                models.CustomerAdvancePayment.customer_id == customer_id,
                models.CustomerAdvancePayment.remaining_amount > 0,
                models.CustomerAdvancePayment.status == 'active'
            )
        ).order_by(models.CustomerAdvancePayment.created_at.asc()).all()
        
        remaining_to_apply = amount
        
        for advance in advance_payments:
            if remaining_to_apply <= 0:
                break
            
            application_amount = min(remaining_to_apply, advance.remaining_amount)
            
            # Create payment allocation
            allocation = models.PaymentAllocation(
                payment_id=advance.payment_id,
                order_id=order_id,
                allocated_amount=application_amount,
                remarks=f"Advance payment application"
            )
            db.add(allocation)
            
            # Update advance payment
            advance.used_amount += application_amount
            advance.remaining_amount -= application_amount
            
            if advance.remaining_amount <= 0:
                advance.status = 'fully_used'
            
            remaining_to_apply -= application_amount
        
        # Update order payment status
        PaymentManager.update_order_payment_status(db, order_id)
        
        db.commit()
        return amount - remaining_to_apply  # Amount actually applied

    @staticmethod
    def process_payment_received(db: Session, payment_id: int):
        """
        MISSING: Complete payment processing with all automatic updates
        """
        payment = db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()
        if not payment:
            return
        
        # Update customer credit usage
        customer = db.query(models.Customer).filter(models.Customer.customer_id == payment.customer_id).first()
        if customer:
            # Get all allocations for this payment
            allocations = db.query(models.PaymentAllocation).filter(
                models.PaymentAllocation.payment_id == payment_id
            ).all()
            
            total_allocated = sum(allocation.allocated_amount for allocation in allocations)
            
            # Reduce customer's credit used
            customer.credit_used = max(0, customer.credit_used - total_allocated)
            
            # Update outstanding for each order
            for allocation in allocations:
                PaymentManager.update_order_payment_status(db, allocation.order_id)
                
                # Update customer outstanding record
                outstanding = db.query(models.CustomerOutstanding).filter(
                    models.CustomerOutstanding.order_id == allocation.order_id
                ).first()
                
                if outstanding:
                    outstanding.paid_amount += allocation.allocated_amount
                    outstanding.outstanding_amount = max(0, outstanding.outstanding_amount - allocation.allocated_amount)
                    
                    if outstanding.outstanding_amount <= 0:
                        outstanding.status = 'paid'
                    elif outstanding.paid_amount > 0:
                        outstanding.status = 'partial'
        
        db.commit()

class DiscountManager:
    """Handles discount scheme application and tracking"""
    
    @staticmethod
    def apply_eligible_discounts(db: Session, order: models.Order, order_items: List[models.OrderItem]) -> float:
        """
        Apply all eligible discounts to an order
        Returns total discount amount applied
        """
        total_discount = 0
        
        # Get active discount schemes
        active_schemes = db.query(models.DiscountScheme).filter(
            and_(
                models.DiscountScheme.is_active == True,
                models.DiscountScheme.valid_from <= datetime.utcnow(),
                models.DiscountScheme.valid_until >= datetime.utcnow()
            )
        ).all()
        
        for scheme in active_schemes:
            discount_amount = DiscountManager.calculate_discount(db, scheme, order, order_items)
            
            if discount_amount > 0:
                # Apply the discount
                applied_discount = models.AppliedDiscount(
                    scheme_id=scheme.scheme_id,
                    order_id=order.order_id,
                    customer_id=order.customer_id,
                    discount_amount=discount_amount,
                    original_amount=order.gross_amount,
                    final_amount=order.gross_amount - discount_amount
                )
                db.add(applied_discount)
                
                # Update scheme usage
                scheme.current_usage_count += 1
                
                # Update customer usage if specific targeting
                customer_usage = db.query(models.DiscountCustomer).filter(
                    and_(
                        models.DiscountCustomer.scheme_id == scheme.scheme_id,
                        models.DiscountCustomer.customer_id == order.customer_id
                    )
                ).first()
                
                if customer_usage:
                    customer_usage.usage_count += 1
                
                total_discount += discount_amount
        
        db.commit()
        return total_discount
    
    @staticmethod
    def calculate_discount(db: Session, scheme: models.DiscountScheme, order: models.Order, order_items: List[models.OrderItem]) -> float:
        """Calculate discount amount for a specific scheme"""
        
        # Check if customer is eligible
        if not DiscountManager.is_customer_eligible(db, scheme, order.customer_id):
            return 0
        
        # Check minimum order value
        if scheme.min_order_value and order.gross_amount < scheme.min_order_value:
            return 0
        
        # Check minimum quantity
        total_quantity = sum(item.quantity for item in order_items)
        if scheme.min_quantity and total_quantity < scheme.min_quantity:
            return 0
        
        # Calculate discount based on type
        if scheme.discount_type == 'percentage':
            discount = order.gross_amount * (scheme.discount_value / 100)
        elif scheme.discount_type == 'fixed_amount':
            discount = scheme.discount_value
        else:
            discount = 0  # Complex discount types can be implemented
        
        # Apply maximum discount cap
        if scheme.max_discount_amount:
            discount = min(discount, scheme.max_discount_amount)
        
        return discount
    
    @staticmethod
    def is_customer_eligible(db: Session, scheme: models.DiscountScheme, customer_id: int) -> bool:
        """Check if customer is eligible for a discount scheme"""
        
        # Check usage limits
        if scheme.max_uses_per_customer:
            customer_usage = db.query(models.DiscountCustomer).filter(
                and_(
                    models.DiscountCustomer.scheme_id == scheme.scheme_id,
                    models.DiscountCustomer.customer_id == customer_id
                )
            ).first()
            
            if customer_usage and customer_usage.usage_count >= scheme.max_uses_per_customer:
                return False
        
        # Check total usage limit
        if scheme.total_usage_limit and scheme.current_usage_count >= scheme.total_usage_limit:
            return False
        
        # Check specific customer targeting
        if scheme.target_type == 'specific_customers':
            specific_customer = db.query(models.DiscountCustomer).filter(
                and_(
                    models.DiscountCustomer.scheme_id == scheme.scheme_id,
                    models.DiscountCustomer.customer_id == customer_id
                )
            ).first()
            
            if not specific_customer:
                return False
        
        # Check customer type targeting
        elif scheme.target_type == 'customer_type' and scheme.target_customer_types:
            customer = db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()
            if customer:
                target_types = json.loads(scheme.target_customer_types) if isinstance(scheme.target_customer_types, str) else scheme.target_customer_types
                if customer.customer_type not in target_types:
                    return False
        
        return True

class ChallanManager:
    """MISSING: Handle challan/dispatch business logic"""
    
    @staticmethod
    def create_challan_from_order(db: Session, order_id: int, user_id: int = None, partial_items: List[Dict] = None):
        """Create challan from order with optional partial dispatch"""
        
        order = db.query(models.Order).filter(models.Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Generate challan number
        import uuid
        challan_number = f"CH{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Create challan
        challan = models.Challan(
            order_id=order_id,
            customer_id=order.customer_id,
            challan_number=challan_number,
            prepared_by=user_id,
            status='prepared'
        )
        db.add(challan)
        db.flush()  # Get challan_id
        
        # Get order items
        order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
        
        total_weight = 0
        total_packages = 0
        
        for order_item in order_items:
            # Check if this is partial dispatch
            dispatched_qty = order_item.quantity
            if partial_items:
                partial_item = next((item for item in partial_items if item['order_item_id'] == order_item.order_item_id), None)
                if partial_item:
                    dispatched_qty = partial_item['dispatched_quantity']
            
            # Get batch and product details
            batch = db.query(models.Batch).filter(models.Batch.batch_id == order_item.batch_id).first()
            product = db.query(models.Product).filter(models.Product.product_id == batch.product_id).first()
            
            # Create challan item
            challan_item = models.ChallanItem(
                challan_id=challan.challan_id,
                order_item_id=order_item.order_item_id,
                batch_id=order_item.batch_id,
                ordered_quantity=order_item.quantity,
                dispatched_quantity=dispatched_qty,
                pending_quantity=order_item.quantity - dispatched_qty,
                product_name=product.product_name,
                batch_number=batch.batch_number,
                expiry_date=batch.expiry_date,
                unit_price=order_item.unit_price
            )
            db.add(challan_item)
            
            # Calculate totals
            if product.weight:
                total_weight += product.weight * dispatched_qty
            total_packages += 1
        
        # Update challan totals
        challan.total_weight = total_weight
        challan.total_packages = total_packages
        
        # Create initial tracking entry
        initial_tracking = models.ChallanTracking(
            challan_id=challan.challan_id,
            location="Warehouse",
            status="prepared",
            updated_by=user_id,
            remarks="Challan prepared and ready for dispatch"
        )
        db.add(initial_tracking)
        
        db.commit()
        return challan

    @staticmethod
    def dispatch_challan(db: Session, challan_id: int, dispatch_details: Dict, user_id: int = None):
        """FIXED: Complete challan dispatch with real-time updates"""
        
        challan = db.query(models.Challan).filter(models.Challan.challan_id == challan_id).first()
        if not challan:
            raise ValueError(f"Challan {challan_id} not found")
        
        if challan.status != 'prepared':
            raise ValueError(f"Can only dispatch prepared challans. Current status: {challan.status}")
        
        try:
            # 1. Update challan with dispatch details
            challan.status = 'dispatched'
            challan.dispatch_date = date.today()
            challan.dispatch_time = datetime.utcnow()
            challan.dispatched_by = user_id
            
            # Update transport details
            for key, value in dispatch_details.items():
                if hasattr(challan, key):
                    setattr(challan, key, value)
            
            # 2. Create dispatch tracking entry
            dispatch_tracking = models.ChallanTracking(
                challan_id=challan_id,
                location="Dispatched from Warehouse",
                status="dispatched",
                updated_by=user_id,
                remarks=f"Dispatched via {dispatch_details.get('transport_company', 'N/A')}"
            )
            db.add(dispatch_tracking)
            
            # 3. Update order status automatically (REAL-TIME FIX)
            order = db.query(models.Order).filter(models.Order.order_id == challan.order_id).first()
            if order:
                order.status = 'dispatched'
                order.dispatch_date = date.today()
            
            # 4. Update inventory reservations automatically
            challan_items = db.query(models.ChallanItem).filter(models.ChallanItem.challan_id == challan_id).all()
            for item in challan_items:
                # Create inventory transaction for dispatch
                inventory_transaction = models.InventoryTransaction(
                    batch_id=item.batch_id,
                    transaction_type='dispatch',
                    quantity_change=-item.dispatched_quantity,
                    reference_type='challan_dispatch',
                    reference_id=challan_id,
                    quantity_before=0,  # Will be calculated by update_batch_status
                    quantity_after=0,   # Will be calculated by update_batch_status
                    performed_by=user_id,
                    remarks=f"Challan dispatch - {item.dispatched_quantity} units",
                    is_automatic=True
                )
                db.add(inventory_transaction)
                
                # Update batch inventory status (same as inventory system)
                InventoryManager.update_batch_status(db, item.batch_id)
            
            db.commit()
            return challan
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to dispatch challan: {str(e)}")
    
    @staticmethod
    def deliver_challan(db: Session, challan_id: int, delivery_info: Dict, user_id: int = None):
        """FIXED: Complete challan delivery with real-time updates"""
        
        challan = db.query(models.Challan).filter(models.Challan.challan_id == challan_id).first()
        if not challan:
            raise ValueError(f"Challan {challan_id} not found")
        
        if challan.status != 'dispatched':
            raise ValueError(f"Can only deliver dispatched challans. Current status: {challan.status}")
        
        try:
            # 1. Update challan status
            challan.status = 'delivered'
            challan.delivery_time = datetime.utcnow()
            
            # Update delivery details
            for key, value in delivery_info.items():
                if hasattr(challan, key):
                    setattr(challan, key, value)
            
            # 2. Create delivery confirmation record (REAL-TIME FIX)
            delivery_confirmation = models.DeliveryConfirmation(
                challan_id=challan_id,
                order_id=challan.order_id,
                customer_id=challan.customer_id,
                is_delivered=True,
                delivery_date=date.today(),
                delivery_time=datetime.utcnow().time(),
                confirmed_by=user_id,
                delivery_notes=delivery_info.get('delivery_notes', ''),
                customer_satisfied=delivery_info.get('customer_satisfied', True),
                confirmation_method='manual'
            )
            db.add(delivery_confirmation)
            
            # 3. Update order status automatically (REAL-TIME FIX)
            order = db.query(models.Order).filter(models.Order.order_id == challan.order_id).first()
            if order:
                order.status = 'delivered'
                order.delivery_status = 'delivered'
                order.delivery_date = date.today()
                order.delivery_notes = delivery_info.get('delivery_notes', '')
            
            # 4. Create delivery tracking entry
            delivery_tracking = models.ChallanTracking(
                challan_id=challan_id,
                location="Delivered to Customer",
                status="delivered",
                updated_by=user_id,
                remarks=f"Delivered successfully. Customer satisfied: {delivery_info.get('customer_satisfied', True)}"
            )
            db.add(delivery_tracking)
            
            db.commit()
            return {"challan": challan, "delivery_confirmation": delivery_confirmation}
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to deliver challan: {str(e)}")


class StockAdjustmentManager:
    """NEW: Handle stock adjustments with real-time updates"""
    
    @staticmethod
    def process_stock_adjustment(db: Session, batch_id: int, adjustment_quantity: int, adjustment_type: str, reason: str, user_id: int = None):
        """Process stock adjustment with complete real-time updates"""
        
        try:
            # Get current batch status
            current_status = InventoryManager.get_batch_status(db, batch_id)
            quantity_before = current_status.current_quantity
            quantity_after = quantity_before + adjustment_quantity
            
            # Create inventory transaction
            inventory_transaction = models.InventoryTransaction(
                batch_id=batch_id,
                transaction_type='adjustment',
                quantity_change=adjustment_quantity,
                reference_type='stock_adjustment',
                reference_id=None,  # Will be set after creating stock adjustment record
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                performed_by=user_id,
                remarks=f"Stock adjustment: {reason}",
                is_automatic=False  # Manual adjustment
            )
            db.add(inventory_transaction)
            db.flush()  # Get transaction_id
            
            # Create stock adjustment record
            stock_adjustment = models.StockAdjustment(
                batch_id=batch_id,
                adjustment_type=adjustment_type,
                adjustment_quantity=adjustment_quantity,
                reason=reason,
                adjusted_by=user_id,
                inventory_transaction_id=inventory_transaction.transaction_id
            )
            db.add(stock_adjustment)
            db.flush()  # Get stock_adjustment_id
            
            # Update reference_id in inventory transaction
            inventory_transaction.reference_id = stock_adjustment.stock_adjustment_id
            
            # Update batch inventory status (same as inventory system)
            InventoryManager.update_batch_status(db, batch_id)
            
            # Create inventory movement for backward compatibility
            inventory_movement = models.InventoryMovement(
                batch_id=batch_id,
                movement_type='adjustment',
                quantity=abs(adjustment_quantity),
                reference=f"Stock Adjustment: {reason}"
            )
            db.add(inventory_movement)
            
            db.commit()
            return {"stock_adjustment": stock_adjustment, "inventory_transaction": inventory_transaction}
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to process stock adjustment: {str(e)}")

class BusinessLogicService:
    """Main service class that orchestrates all business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_manager = InventoryManager()
        self.payment_manager = PaymentManager()
        self.discount_manager = DiscountManager()
    
    def process_complete_order(self, order_data: dict, order_items: List[dict], user_id: int = None) -> dict:
        """
        Complete order processing with inventory, discounts, and accounting
        This is the main function called when an order is placed
        """
        try:
            # 1. Create the order
            order = models.Order(**order_data)
            self.db.add(order)
            self.db.flush()  # Get order_id
            
            # 2. Create order items
            order_item_objects = []
            for item_data in order_items:
                item_data['order_id'] = order.order_id
                order_item = models.OrderItem(**item_data)
                self.db.add(order_item)
                order_item_objects.append(order_item)
            
            self.db.flush()  # Get order_item_ids
            
            # 3. Apply discounts
            total_discount = self.discount_manager.apply_eligible_discounts(
                self.db, order, order_item_objects
            )
            
            # Update order with discount
            order.discount = total_discount
            order.final_amount = order.gross_amount - total_discount + order.tax_amount
            
            # 4. Process inventory updates
            inventory_transactions = self.inventory_manager.process_order_inventory(
                self.db, order_item_objects, user_id
            )
            
            # 5. Create accounting entries
            self._create_order_journal_entries(order, order_item_objects)
            
            # 6. Update customer outstanding
            self._update_customer_outstanding(order)
            
            self.db.commit()
            
            return {
                'order_id': order.order_id,
                'final_amount': order.final_amount,
                'discount_applied': total_discount,
                'inventory_transactions': len(inventory_transactions),
                'status': 'success'
            }
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def _create_order_journal_entries(self, order: models.Order, order_items: List[models.OrderItem]):
        """Create accounting journal entries for an order"""
        
        # Sales Revenue Entry (Credit)
        revenue_entry = models.JournalEntry(
            transaction_type='sale',
            order_id=order.order_id,
            account_name='Sales Revenue',
            account_type='income',
            credit_amount=order.gross_amount,
            debit_amount=0,
            reference=f"Order #{order.order_id}",
            remarks=f"Sales revenue for order {order.order_id}"
        )
        self.db.add(revenue_entry)
        
        # Accounts Receivable Entry (Debit)
        receivable_entry = models.JournalEntry(
            transaction_type='sale',
            order_id=order.order_id,
            account_name='Accounts Receivable',
            account_type='asset',
            debit_amount=order.final_amount,
            credit_amount=0,
            reference=f"Order #{order.order_id}",
            remarks=f"Accounts receivable for order {order.order_id}"
        )
        self.db.add(receivable_entry)
        
        # Tax Entries if applicable
        if order.tax_amount > 0:
            tax_entry = models.JournalEntry(
                transaction_type='sale',
                order_id=order.order_id,
                account_name='Sales Tax Payable',
                account_type='liability',
                credit_amount=order.tax_amount,
                debit_amount=0,
                reference=f"Order #{order.order_id}",
                remarks=f"Sales tax for order {order.order_id}"
            )
            self.db.add(tax_entry)
    
    def _update_customer_outstanding(self, order: models.Order):
        """Update customer outstanding balances"""
        outstanding = models.CustomerOutstanding(
            customer_id=order.customer_id,
            order_id=order.order_id,
            total_amount=order.final_amount,
            outstanding_amount=order.final_amount,
            invoice_date=order.order_date.date(),
            due_date=order.order_date.date()  # Can be calculated based on payment terms
        )
        self.db.add(outstanding) 