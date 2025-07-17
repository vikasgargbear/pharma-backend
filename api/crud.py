from sqlalchemy.orm import Session
# Handle both package and direct imports
try:
    from . import models, schemas
except ImportError:
    import models
    import schemas
from datetime import datetime, timedelta, date
from typing import List, Dict
from sqlalchemy import func, and_
import json

# NOTE: This file contains CRUD functions for various models.
# Some functions reference models that don't exist in the current database:
# - PaymentAllocation, CustomerAdvancePayment, BatchLocation, CDSCOCompliance
# - Cart, CartItem, ChallanTracking, CustomerCreditNote, CustomerOutstanding
# - DiscountScheme, InventoryTransaction, JournalEntry, LicenseDocument
# - MedicalRepresentative, PriceHistory, PurchaseItem, PurchaseReturn
# - PurchaseReturnItem, RegulatoryLicense, StateDrugControllerCompliance
# - StorageLocation, VendorPayment, BatchInventoryStatus, AppliedDiscount
# - LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, LoyaltyRedemption
# - UPIPayment, FileUpload
# 
# These functions will fail if called. Only use functions for models that exist
# in the database (see models.py for the current list of available models).

# ----------------- PRODUCTS -----------------

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.product_id == product_id).first()

def update_product(db: Session, product_id: int, updates: schemas.ProductCreate):
    db_product = get_product(db, product_id)
    if db_product:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product

# ----------------- CUSTOMERS -----------------

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.customer_id == customer_id).first()

def update_customer(db: Session, customer_id: int, updates: schemas.CustomerCreate):
    db_customer = get_customer(db, customer_id)
    if db_customer:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_customer, key, value)
        db.commit()
        db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)
    if db_customer:
        db.delete(db_customer)
        db.commit()
    return db_customer

# ----------------- ENHANCED ORDERS WITH BUSINESS LOGIC -----------------

def create_order_with_business_logic(db: Session, order: schemas.OrderCreate, order_items: List[schemas.OrderItemCreate], user_id: int = None):
    """Create order with automatic inventory updates, discounts, and accounting"""
    from .business_logic import BusinessLogicService
    
    business_service = BusinessLogicService(db)
    
    # Convert Pydantic models to dict for business logic processing
    order_data = order.model_dump()
    order_items_data = [item.model_dump() for item in order_items]
    
    return business_service.process_complete_order(order_data, order_items_data, user_id)

def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.order_id == order_id).first()

def update_order(db: Session, order_id: int, updates: schemas.OrderCreate):
    db_order = get_order(db, order_id)
    if db_order:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_order, key, value)
        db.commit()
        db.refresh(db_order)
    return db_order

def delete_order(db: Session, order_id: int):
    db_order = get_order(db, order_id)
    if db_order:
        db.delete(db_order)
        db.commit()
    return db_order

# ----------------- ORDER ITEMS -----------------

def create_order_item(db: Session, item: schemas.OrderItemCreate):
    db_item = models.OrderItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_order_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.OrderItem).offset(skip).limit(limit).all()

def get_order_item(db: Session, order_item_id: int):
    return db.query(models.OrderItem).filter(models.OrderItem.order_item_id == order_item_id).first()

def update_order_item(db: Session, order_item_id: int, updates: schemas.OrderItemCreate):
    db_item = get_order_item(db, order_item_id)
    if db_item:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_order_item(db: Session, order_item_id: int):
    db_item = get_order_item(db, order_item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

# ----------------- BATCHES -----------------

def create_batch(db: Session, batch: schemas.BatchCreate):
    db_batch = models.Batch(**batch.model_dump())
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

def get_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Batch).offset(skip).limit(limit).all()

def get_batch(db: Session, batch_id: int):
    return db.query(models.Batch).filter(models.Batch.batch_id == batch_id).first()

def update_batch(db: Session, batch_id: int, updates: schemas.BatchCreate):
    db_batch = get_batch(db, batch_id)
    if db_batch:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_batch, key, value)
        db.commit()
        db.refresh(db_batch)
    return db_batch

def delete_batch(db: Session, batch_id: int):
    db_batch = get_batch(db, batch_id)
    if db_batch:
        db.delete(db_batch)
        db.commit()
    return db_batch

# ----------------- ENHANCED PAYMENTS WITH ALLOCATION -----------------

def create_payment_with_allocation(
    db: Session, 
    customer_id: int,
    amount: float,
    payment_mode: str,
    order_ids: List[int] = None,
    payment_type: str = 'order_payment',
    **kwargs
):
    """Create payment with automatic allocation to orders"""
    from .business_logic import PaymentManager
    
    return PaymentManager.create_payment_with_allocation(
        db, customer_id, amount, payment_mode, order_ids, payment_type, **kwargs
    )

def apply_advance_payment_to_order(db: Session, customer_id: int, order_id: int, amount: float):
    """Apply customer's advance payment to an order"""
    from .business_logic import PaymentManager
    
    return PaymentManager.apply_advance_payment(db, customer_id, order_id, amount)

def create_payment(db: Session, payment: schemas.PaymentCreate):
    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Payment).offset(skip).limit(limit).all()

def get_payment(db: Session, payment_id: int):
    return db.query(models.Payment).filter(models.Payment.payment_id == payment_id).first()

def update_payment(db: Session, payment_id: int, updates: schemas.PaymentCreate):
    db_payment = get_payment(db, payment_id)
    if db_payment:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

def delete_payment(db: Session, payment_id: int):
    db_payment = get_payment(db, payment_id)
    if db_payment:
        db.delete(db_payment)
        db.commit()
    return db_payment

# ----------------- PAYMENT ALLOCATIONS -----------------

def create_payment_allocation(db: Session, allocation: schemas.PaymentAllocationCreate):
    db_allocation = models.PaymentAllocation(**allocation.model_dump())
    db.add(db_allocation)
    db.commit()
    db.refresh(db_allocation)
    return db_allocation

def get_payment_allocations(db: Session, payment_id: int = None, order_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PaymentAllocation)
    if payment_id:
        query = query.filter(models.PaymentAllocation.payment_id == payment_id)
    if order_id:
        query = query.filter(models.PaymentAllocation.order_id == order_id)
    return query.offset(skip).limit(limit).all()

def get_payment_allocation(db: Session, allocation_id: int):
    return db.query(models.PaymentAllocation).filter(models.PaymentAllocation.allocation_id == allocation_id).first()

# ----------------- CUSTOMER ADVANCE PAYMENTS -----------------

def create_customer_advance_payment(db: Session, advance: schemas.CustomerAdvancePaymentCreate):
    db_advance = models.CustomerAdvancePayment(**advance.model_dump())
    db.add(db_advance)
    db.commit()
    db.refresh(db_advance)
    return db_advance

def get_customer_advance_payments(db: Session, customer_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.CustomerAdvancePayment).filter(
        models.CustomerAdvancePayment.customer_id == customer_id
    ).offset(skip).limit(limit).all()

def get_customer_advance_balance(db: Session, customer_id: int):
    """Get total advance balance for a customer"""
    total_advance = db.query(func.sum(models.CustomerAdvancePayment.remaining_amount)).filter(
        and_(
            models.CustomerAdvancePayment.customer_id == customer_id,
            models.CustomerAdvancePayment.status == 'active'
        )
    ).scalar() or 0
    return total_advance

# ----------------- INVENTORY MOVEMENTS -----------------

def create_inventory_movement(db: Session, movement: schemas.InventoryMovementCreate):
    db_movement = models.InventoryMovement(**movement.model_dump())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

def get_inventory_movements(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.InventoryMovement).offset(skip).limit(limit).all()

def get_inventory_movement(db: Session, movement_id: int):
    return db.query(models.InventoryMovement).filter(models.InventoryMovement.movement_id == movement_id).first()

def update_inventory_movement(db: Session, movement_id: int, updates: schemas.InventoryMovementCreate):
    db_movement = get_inventory_movement(db, movement_id)
    if db_movement:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_movement, key, value)
        db.commit()
        db.refresh(db_movement)
    return db_movement

def delete_inventory_movement(db: Session, movement_id: int):
    db_movement = get_inventory_movement(db, movement_id)
    if db_movement:
        db.delete(db_movement)
        db.commit()
    return db_movement

# ----------------- SALES RETURNS -----------------

def create_sales_return(db: Session, sales_return: schemas.SalesReturnCreate):
    db_return = models.SalesReturn(**sales_return.model_dump())
    db.add(db_return)
    db.commit()
    db.refresh(db_return)
    return db_return

def get_sales_returns(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SalesReturn).offset(skip).limit(limit).all()

def get_sales_return(db: Session, return_id: int):
    return db.query(models.SalesReturn).filter(models.SalesReturn.return_id == return_id).first()

def update_sales_return(db: Session, return_id: int, updates: schemas.SalesReturnCreate):
    db_return = get_sales_return(db, return_id)
    if db_return:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_return, key, value)
        db.commit()
        db.refresh(db_return)
    return db_return

def delete_sales_return(db: Session, return_id: int):
    db_return = get_sales_return(db, return_id)
    if db_return:
        db.delete(db_return)
        db.commit()
    return db_return

# ----------------- USERS -----------------

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def update_user(db: Session, user_id: int, updates: schemas.UserCreate):
    db_user = get_user(db, user_id)
    if db_user:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# ----------------- PURCHASES -----------------

def create_purchase(db: Session, purchase: schemas.PurchaseCreate):
    db_purchase = models.Purchase(**purchase.model_dump())
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

def get_purchases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Purchase).offset(skip).limit(limit).all()

def get_purchase(db: Session, purchase_id: int):
    return db.query(models.Purchase).filter(models.Purchase.purchase_id == purchase_id).first()

def update_purchase(db: Session, purchase_id: int, updates: schemas.PurchaseCreate):
    db_purchase = get_purchase(db, purchase_id)
    if db_purchase:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_purchase, key, value)
        db.commit()
        db.refresh(db_purchase)
    return db_purchase

def delete_purchase(db: Session, purchase_id: int):
    db_purchase = get_purchase(db, purchase_id)
    if db_purchase:
        db.delete(db_purchase)
        db.commit()
    return db_purchase

# ----------------- PURCHASE ITEMS -----------------

def create_purchase_item(db: Session, purchase_item: schemas.PurchaseItemCreate):
    db_item = models.PurchaseItem(**purchase_item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_purchase_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PurchaseItem).offset(skip).limit(limit).all()

def get_purchase_item(db: Session, purchase_item_id: int):
    return db.query(models.PurchaseItem).filter(models.PurchaseItem.purchase_item_id == purchase_item_id).first()

def update_purchase_item(db: Session, purchase_item_id: int, updates: schemas.PurchaseItemCreate):
    db_item = get_purchase_item(db, purchase_item_id)
    if db_item:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_purchase_item(db: Session, purchase_item_id: int):
    db_item = get_purchase_item(db, purchase_item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

# ----------------- TAX ENTRIES -----------------

def create_tax_entry(db: Session, tax_entry: schemas.TaxEntryCreate):
    db_tax = models.TaxEntry(**tax_entry.model_dump())
    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)
    return db_tax

def get_tax_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TaxEntry).offset(skip).limit(limit).all()

def get_tax_entry(db: Session, tax_entry_id: int):
    return db.query(models.TaxEntry).filter(models.TaxEntry.tax_entry_id == tax_entry_id).first()

def update_tax_entry(db: Session, tax_entry_id: int, updates: schemas.TaxEntryCreate):
    db_tax = get_tax_entry(db, tax_entry_id)
    if db_tax:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_tax, key, value)
        db.commit()
        db.refresh(db_tax)
    return db_tax

def delete_tax_entry(db: Session, tax_entry_id: int):
    db_tax = get_tax_entry(db, tax_entry_id)
    if db_tax:
        db.delete(db_tax)
        db.commit()
    return db_tax

# ----------------- VENDOR PAYMENTS -----------------

def create_vendor_payment(db: Session, payment: schemas.VendorPaymentCreate):
    db_payment = models.VendorPayment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_vendor_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.VendorPayment).offset(skip).limit(limit).all()

def get_vendor_payment(db: Session, vendor_payment_id: int):
    return db.query(models.VendorPayment).filter(models.VendorPayment.vendor_payment_id == vendor_payment_id).first()

def update_vendor_payment(db: Session, vendor_payment_id: int, updates: schemas.VendorPaymentCreate):
    db_payment = get_vendor_payment(db, vendor_payment_id)
    if db_payment:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

def delete_vendor_payment(db: Session, vendor_payment_id: int):
    db_payment = get_vendor_payment(db, vendor_payment_id)
    if db_payment:
        db.delete(db_payment)
        db.commit()
    return db_payment

# ----------------- JOURNAL ENTRIES -----------------

def create_journal_entry(db: Session, entry: schemas.JournalEntryCreate):
    db_entry = models.JournalEntry(**entry.model_dump())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_journal_entries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.JournalEntry).offset(skip).limit(limit).all()

def get_journal_entry(db: Session, entry_id: int):
    return db.query(models.JournalEntry).filter(models.JournalEntry.entry_id == entry_id).first()

def update_journal_entry(db: Session, entry_id: int, updates: schemas.JournalEntryCreate):
    db_entry = get_journal_entry(db, entry_id)
    if db_entry:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_entry, key, value)
        db.commit()
        db.refresh(db_entry)
    return db_entry

def delete_journal_entry(db: Session, entry_id: int):
    db_entry = get_journal_entry(db, entry_id)
    if db_entry:
        db.delete(db_entry)
        db.commit()
    return db_entry

# ----------------- CART -----------------

def create_cart(db: Session, cart: schemas.CartCreate):
    db_cart = models.Cart(**cart.model_dump())
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart

def get_cart_by_user(db: Session, user_id: str):
    return db.query(models.Cart).filter(models.Cart.user_id == user_id).first()

def get_cart(db: Session, cart_id: int):
    return db.query(models.Cart).filter(models.Cart.cart_id == cart_id).first()

def update_cart(db: Session, cart_id: int, updates: schemas.CartCreate):
    db_cart = get_cart(db, cart_id)
    if db_cart:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_cart, key, value)
        db_cart.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_cart)
    return db_cart

def delete_cart(db: Session, cart_id: int):
    db_cart = get_cart(db, cart_id)
    if db_cart:
        db.delete(db_cart)
        db.commit()
    return db_cart

# ----------------- CART ITEMS -----------------

def create_cart_item(db: Session, cart_item: schemas.CartItemCreate):
    db_cart_item = models.CartItem(**cart_item.model_dump())
    db.add(db_cart_item)
    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item

def get_cart_items(db: Session, cart_id: int):
    return db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()

def get_cart_item(db: Session, cart_item_id: int):
    return db.query(models.CartItem).filter(models.CartItem.cart_item_id == cart_item_id).first()

def update_cart_item(db: Session, cart_item_id: int, updates: schemas.CartItemCreate):
    db_cart_item = get_cart_item(db, cart_item_id)
    if db_cart_item:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_cart_item, key, value)
        db.commit()
        db.refresh(db_cart_item)
    return db_cart_item

def delete_cart_item(db: Session, cart_item_id: int):
    db_cart_item = get_cart_item(db, cart_item_id)
    if db_cart_item:
        db.delete(db_cart_item)
        db.commit()
    return db_cart_item

# ----------------- SUPPLIERS -----------------

def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    db_supplier = models.Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def get_suppliers(db: Session, skip: int = 0, limit: int = 100, is_active: bool = None):
    query = db.query(models.Supplier)
    if is_active is not None:
        query = query.filter(models.Supplier.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_supplier(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.supplier_id == supplier_id).first()

def update_supplier(db: Session, supplier_id: int, updates: schemas.SupplierCreate):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_supplier, key, value)
        db.commit()
        db.refresh(db_supplier)
    return db_supplier

def delete_supplier(db: Session, supplier_id: int):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier:
        db.delete(db_supplier)
        db.commit()
    return db_supplier

# ----------------- MEDICAL REPRESENTATIVES -----------------

def create_medical_representative(db: Session, mr: schemas.MedicalRepresentativeCreate):
    db_mr = models.MedicalRepresentative(**mr.model_dump())
    db.add(db_mr)
    db.commit()
    db.refresh(db_mr)
    return db_mr

def get_medical_representatives(db: Session, skip: int = 0, limit: int = 100, is_active: bool = None):
    query = db.query(models.MedicalRepresentative)
    if is_active is not None:
        query = query.filter(models.MedicalRepresentative.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_medical_representative(db: Session, mr_id: int):
    return db.query(models.MedicalRepresentative).filter(models.MedicalRepresentative.mr_id == mr_id).first()

def update_medical_representative(db: Session, mr_id: int, updates: schemas.MedicalRepresentativeCreate):
    db_mr = get_medical_representative(db, mr_id)
    if db_mr:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_mr, key, value)
        db.commit()
        db.refresh(db_mr)
    return db_mr

def delete_medical_representative(db: Session, mr_id: int):
    db_mr = get_medical_representative(db, mr_id)
    if db_mr:
        db.delete(db_mr)
        db.commit()
    return db_mr

# ----------------- REGULATORY LICENSES -----------------

def create_regulatory_license(db: Session, license: schemas.RegulatoryLicenseCreate):
    db_license = models.RegulatoryLicense(**license.model_dump())
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def get_regulatory_licenses(db: Session, entity_type: str = None, entity_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.RegulatoryLicense)
    if entity_type:
        query = query.filter(models.RegulatoryLicense.entity_type == entity_type)
    if entity_id:
        query = query.filter(models.RegulatoryLicense.entity_id == entity_id)
    if status:
        query = query.filter(models.RegulatoryLicense.status == status)
    return query.offset(skip).limit(limit).all()

def get_expiring_licenses(db: Session, days_ahead: int = 60):
    """Get licenses expiring within specified days"""
    from datetime import datetime, timedelta
    expiry_threshold = datetime.now().date() + timedelta(days=days_ahead)
    
    return db.query(models.RegulatoryLicense).filter(
        and_(
            models.RegulatoryLicense.expiry_date <= expiry_threshold,
            models.RegulatoryLicense.status == 'active'
        )
    ).all()

# ----------------- PRICE HISTORY -----------------

def create_price_history(db: Session, price_history: schemas.PriceHistoryCreate):
    db_price = models.PriceHistory(**price_history.model_dump())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

def get_price_history(db: Session, product_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PriceHistory)
    if product_id:
        query = query.filter(models.PriceHistory.product_id == product_id)
    return query.order_by(models.PriceHistory.effective_date.desc()).offset(skip).limit(limit).all()

def get_price_history_record(db: Session, price_history_id: int):
    return db.query(models.PriceHistory).filter(models.PriceHistory.price_history_id == price_history_id).first()

# ----------------- ENHANCED DISCOUNT SCHEMES -----------------

def create_discount_scheme(db: Session, scheme: schemas.DiscountSchemeCreate):
    db_scheme = models.DiscountScheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return db_scheme

def get_discount_schemes(db: Session, is_active: bool = None, skip: int = 0, limit: int = 100):
    query = db.query(models.DiscountScheme)
    if is_active is not None:
        query = query.filter(models.DiscountScheme.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_discount_scheme(db: Session, scheme_id: int):
    return db.query(models.DiscountScheme).filter(models.DiscountScheme.scheme_id == scheme_id).first()

def update_discount_scheme(db: Session, scheme_id: int, updates: schemas.DiscountSchemeCreate):
    db_scheme = get_discount_scheme(db, scheme_id)
    if db_scheme:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_scheme, key, value)
        db.commit()
        db.refresh(db_scheme)
    return db_scheme

def delete_discount_scheme(db: Session, scheme_id: int):
    db_scheme = get_discount_scheme(db, scheme_id)
    if db_scheme:
        db.delete(db_scheme)
        db.commit()
    return db_scheme

# ----------------- APPLIED DISCOUNTS -----------------

def get_applied_discounts(db: Session, order_id: int = None, customer_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.AppliedDiscount)
    if order_id:
        query = query.filter(models.AppliedDiscount.order_id == order_id)
    if customer_id:
        query = query.filter(models.AppliedDiscount.customer_id == customer_id)
    return query.offset(skip).limit(limit).all()

# ----------------- CUSTOMER CREDIT NOTES -----------------

def create_customer_credit_note(db: Session, credit_note: schemas.CustomerCreditNoteCreate):
    db_credit = models.CustomerCreditNote(**credit_note.model_dump())
    db.add(db_credit)
    db.commit()
    db.refresh(db_credit)
    return db_credit

def get_customer_credit_notes(db: Session, customer_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.CustomerCreditNote)
    if customer_id:
        query = query.filter(models.CustomerCreditNote.customer_id == customer_id)
    return query.offset(skip).limit(limit).all()

def get_customer_credit_note(db: Session, credit_note_id: int):
    return db.query(models.CustomerCreditNote).filter(models.CustomerCreditNote.credit_note_id == credit_note_id).first()

def update_customer_credit_note(db: Session, credit_note_id: int, updates: schemas.CustomerCreditNoteCreate):
    db_credit = get_customer_credit_note(db, credit_note_id)
    if db_credit:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_credit, key, value)
        db.commit()
        db.refresh(db_credit)
    return db_credit

# ----------------- CUSTOMER OUTSTANDING -----------------

def create_customer_outstanding(db: Session, outstanding: schemas.CustomerOutstandingCreate):
    db_outstanding = models.CustomerOutstanding(**outstanding.model_dump())
    db.add(db_outstanding)
    db.commit()
    db.refresh(db_outstanding)
    return db_outstanding

def get_customer_outstanding(db: Session, customer_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.CustomerOutstanding)
    if customer_id:
        query = query.filter(models.CustomerOutstanding.customer_id == customer_id)
    return query.offset(skip).limit(limit).all()

def get_customer_outstanding_record(db: Session, outstanding_id: int):
    return db.query(models.CustomerOutstanding).filter(models.CustomerOutstanding.outstanding_id == outstanding_id).first()

def update_customer_outstanding(db: Session, outstanding_id: int, updates: schemas.CustomerOutstandingCreate):
    db_outstanding = get_customer_outstanding_record(db, outstanding_id)
    if db_outstanding:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_outstanding, key, value)
        db.commit()
        db.refresh(db_outstanding)
    return db_outstanding

# ----------------- PURCHASE RETURNS -----------------

def create_purchase_return(db: Session, purchase_return: schemas.PurchaseReturnCreate):
    db_return = models.PurchaseReturn(**purchase_return.model_dump())
    db.add(db_return)
    db.commit()
    db.refresh(db_return)
    return db_return

def get_purchase_returns(db: Session, supplier_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PurchaseReturn)
    if supplier_id:
        query = query.filter(models.PurchaseReturn.supplier_id == supplier_id)
    return query.offset(skip).limit(limit).all()

def get_purchase_return(db: Session, return_id: int):
    return db.query(models.PurchaseReturn).filter(models.PurchaseReturn.return_id == return_id).first()

def update_purchase_return(db: Session, return_id: int, updates: schemas.PurchaseReturnCreate):
    db_return = get_purchase_return(db, return_id)
    if db_return:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_return, key, value)
        db.commit()
        db.refresh(db_return)
    return db_return

# ----------------- PURCHASE RETURN ITEMS -----------------

def create_purchase_return_item(db: Session, return_item: schemas.PurchaseReturnItemCreate):
    db_item = models.PurchaseReturnItem(**return_item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_purchase_return_items(db: Session, return_id: int):
    return db.query(models.PurchaseReturnItem).filter(models.PurchaseReturnItem.return_id == return_id).all()

def get_purchase_return_item(db: Session, return_item_id: int):
    return db.query(models.PurchaseReturnItem).filter(models.PurchaseReturnItem.return_item_id == return_item_id).first()

# ----------------- STORAGE LOCATIONS -----------------

def create_storage_location(db: Session, location: schemas.StorageLocationCreate):
    db_location = models.StorageLocation(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_storage_locations(db: Session, skip: int = 0, limit: int = 100, is_active: bool = None):
    query = db.query(models.StorageLocation)
    if is_active is not None:
        query = query.filter(models.StorageLocation.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def get_storage_location(db: Session, location_id: int):
    return db.query(models.StorageLocation).filter(models.StorageLocation.location_id == location_id).first()

def update_storage_location(db: Session, location_id: int, updates: schemas.StorageLocationCreate):
    db_location = get_storage_location(db, location_id)
    if db_location:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_location, key, value)
        db.commit()
        db.refresh(db_location)
    return db_location

# ----------------- BATCH LOCATIONS -----------------

def create_batch_location(db: Session, batch_location: schemas.BatchLocationCreate):
    db_batch_location = models.BatchLocation(**batch_location.model_dump())
    db.add(db_batch_location)
    db.commit()
    db.refresh(db_batch_location)
    return db_batch_location

def get_batch_locations(db: Session, batch_id: int = None, location_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BatchLocation)
    if batch_id:
        query = query.filter(models.BatchLocation.batch_id == batch_id)
    if location_id:
        query = query.filter(models.BatchLocation.location_id == location_id)
    return query.offset(skip).limit(limit).all()

def get_batch_location(db: Session, batch_location_id: int):
    return db.query(models.BatchLocation).filter(models.BatchLocation.batch_location_id == batch_location_id).first()

def update_batch_location(db: Session, batch_location_id: int, updates: schemas.BatchLocationCreate):
    db_batch_location = get_batch_location(db, batch_location_id)
    if db_batch_location:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_batch_location, key, value)
        db.commit()
        db.refresh(db_batch_location)
    return db_batch_location

# ----------------- INVENTORY TRANSACTIONS & STATUS -----------------

def get_inventory_transactions(db: Session, batch_id: int = None, transaction_type: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.InventoryTransaction)
    if batch_id:
        query = query.filter(models.InventoryTransaction.batch_id == batch_id)
    if transaction_type:
        query = query.filter(models.InventoryTransaction.transaction_type == transaction_type)
    return query.order_by(models.InventoryTransaction.transaction_date.desc()).offset(skip).limit(limit).all()

def get_batch_inventory_status(db: Session, batch_id: int):
    """Get current inventory status for a batch"""
    from .business_logic import InventoryManager
    return InventoryManager.get_batch_status(db, batch_id)

def get_low_stock_batches(db: Session, limit: int = 50):
    """Get batches with low stock levels"""
    return db.query(models.BatchInventoryStatus).join(
        models.Batch, models.BatchInventoryStatus.batch_id == models.Batch.batch_id
    ).filter(
        models.BatchInventoryStatus.is_low_stock == True
    ).limit(limit).all()

def get_out_of_stock_batches(db: Session, limit: int = 50):
    """Get batches that are out of stock"""
    return db.query(models.BatchInventoryStatus).join(
        models.Batch, models.BatchInventoryStatus.batch_id == models.Batch.batch_id
    ).filter(
        models.BatchInventoryStatus.is_out_of_stock == True
    ).limit(limit).all()

def get_fifo_batch_allocation(db: Session, product_id: int, required_quantity: int):
    """Get FIFO batch allocation for a product"""
    from .business_logic import InventoryManager
    return InventoryManager.get_fifo_batches(db, product_id, required_quantity)

# ----------------- CHALLAN/DISPATCH MANAGEMENT -----------------

def create_challan(db: Session, challan: schemas.ChallanCreate):
    db_challan = models.Challan(**challan.model_dump())
    db.add(db_challan)
    db.commit()
    db.refresh(db_challan)
    return db_challan

def get_challans(db: Session, order_id: int = None, customer_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Challan)
    if order_id:
        query = query.filter(models.Challan.order_id == order_id)
    if customer_id:
        query = query.filter(models.Challan.customer_id == customer_id)
    if status:
        query = query.filter(models.Challan.status == status)
    return query.offset(skip).limit(limit).all()

def get_challan(db: Session, challan_id: int):
    return db.query(models.Challan).filter(models.Challan.challan_id == challan_id).first()

def update_challan(db: Session, challan_id: int, updates: schemas.ChallanCreate):
    db_challan = get_challan(db, challan_id)
    if db_challan:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_challan, key, value)
        db.commit()
        db.refresh(db_challan)
    return db_challan

def create_challan_from_order(db: Session, order_id: int, user_id: int = None, partial_items: List[Dict] = None):
    """Create challan from order using business logic"""
    from .business_logic import ChallanManager
    return ChallanManager.create_challan_from_order(db, order_id, user_id, partial_items)

def dispatch_challan(db: Session, challan_id: int, dispatch_details: Dict, user_id: int = None):
    """Dispatch challan using business logic"""
    from .business_logic import ChallanManager
    return ChallanManager.dispatch_challan(db, challan_id, dispatch_details, user_id)

def get_challan_items(db: Session, challan_id: int):
    return db.query(models.ChallanItem).filter(models.ChallanItem.challan_id == challan_id).all()

def get_challan_tracking(db: Session, challan_id: int):
    return db.query(models.ChallanTracking).filter(
        models.ChallanTracking.challan_id == challan_id
    ).order_by(models.ChallanTracking.timestamp.desc()).all()

def add_challan_tracking(db: Session, tracking: schemas.ChallanTrackingCreate):
    db_tracking = models.ChallanTracking(**tracking.model_dump())
    db.add(db_tracking)
    db.commit()
    db.refresh(db_tracking)
    return db_tracking

# ----------------- MISSING BUSINESS OPERATIONS -----------------

def process_sales_return_inventory(db: Session, return_items: List[Dict], user_id: int = None):
    """Process sales return with automatic inventory updates"""
    from .business_logic import InventoryManager
    return InventoryManager.process_sales_return(db, return_items, user_id)

def process_stock_adjustment(db: Session, adjustments: List[Dict], reason: str, user_id: int = None):
    """Process stock adjustments with audit trail"""
    from .business_logic import InventoryManager
    return InventoryManager.process_stock_adjustment(db, adjustments, reason, user_id)

def get_batch_recommendations(db: Session, product_id: int, required_quantity: int):
    """Get FIFO batch recommendations (not automatic selection)"""
    from .business_logic import InventoryManager
    return InventoryManager.get_fifo_batches(db, product_id, required_quantity)

def get_expiry_alerts(db: Session, days_ahead: int = 30):
    """Get batches expiring within specified days"""
    from .business_logic import InventoryManager
    return InventoryManager.process_expiry_management(db, days_ahead)

def process_payment_with_updates(db: Session, payment_id: int):
    """Process payment with all automatic updates"""
    from .business_logic import PaymentManager
    return PaymentManager.process_payment_received(db, payment_id)

def get_pending_challans(db: Session, limit: int = 50):
    """Get challans ready for dispatch"""
    return db.query(models.Challan).filter(
        models.Challan.status.in_(['prepared', 'ready_for_dispatch'])
    ).limit(limit).all()

def get_customer_pending_deliveries(db: Session, customer_id: int):
    """Get all pending deliveries for a customer"""
    return db.query(models.Challan).filter(
        and_(
            models.Challan.customer_id == customer_id,
            models.Challan.status.in_(['dispatched', 'in_transit'])
        )
    ).all()

# ----------------- ENHANCED REGULATORY LICENSES -----------------

def get_regulatory_license(db: Session, license_id: int):
    return db.query(models.RegulatoryLicense).filter(models.RegulatoryLicense.license_id == license_id).first()

def update_regulatory_license(db: Session, license_id: int, updates: schemas.RegulatoryLicenseCreate):
    db_license = get_regulatory_license(db, license_id)
    if db_license:
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(db_license, key, value)
        db.commit()
        db.refresh(db_license)
    return db_license

def delete_regulatory_license(db: Session, license_id: int):
    db_license = get_regulatory_license(db, license_id)
    if db_license:
        db.delete(db_license)
        db.commit()
    return db_license

def get_customer_active_challans(db: Session, customer_id: int):
    """Get active challans for a customer"""
    return db.query(models.Challan).filter(
        and_(
            models.Challan.customer_id == customer_id,
            models.Challan.status.in_(['dispatched', 'in_transit'])
        )
    ).all()

def create_inventory_transaction(db: Session, transaction: schemas.InventoryTransactionCreate):
    """Create a new inventory transaction"""
    db_transaction = models.InventoryTransaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_batch_inventory_transactions(db: Session, batch_id: int, skip: int = 0, limit: int = 100):
    """Get all inventory transactions for a specific batch"""
    return db.query(models.InventoryTransaction).filter(
        models.InventoryTransaction.batch_id == batch_id
    ).order_by(models.InventoryTransaction.transaction_date.desc()).offset(skip).limit(limit).all()

def update_customer_advance_payment(db: Session, advance_payment_id: int, updates: schemas.CustomerAdvancePaymentCreate):
    """Update customer advance payment"""
    db_advance = get_customer_advance_payment(db, advance_payment_id)
    if db_advance:
        for key, value in updates.model_dump().items():
            setattr(db_advance, key, value)
        db.commit()
        db.refresh(db_advance)
    return db_advance

def get_customer_advance_payment(db: Session, advance_payment_id: int):
    """Get specific advance payment by ID"""
    return db.query(models.CustomerAdvancePayment).filter(
        models.CustomerAdvancePayment.advance_payment_id == advance_payment_id
    ).first()

# ----------------- ENHANCED INDIAN REGULATORY COMPLIANCE -----------------

def create_enhanced_regulatory_license(db: Session, license: schemas.EnhancedRegulatoryLicenseCreate):
    """Create enhanced regulatory license with Indian compliance features"""
    db_license = models.RegulatoryLicense(**license.model_dump())
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license

def get_enhanced_regulatory_licenses(db: Session, entity_type: str = None, state: str = None, license_type: str = None, skip: int = 0, limit: int = 100):
    """Get enhanced regulatory licenses with filtering"""
    query = db.query(models.RegulatoryLicense)
    
    if entity_type:
        query = query.filter(models.RegulatoryLicense.entity_type == entity_type)
    if state:
        query = query.filter(models.RegulatoryLicense.issuing_state == state)
    if license_type:
        query = query.filter(models.RegulatoryLicense.license_type == license_type)
    
    return query.offset(skip).limit(limit).all()

def get_expiring_licenses_enhanced(db: Session, days_ahead: int = 60):
    """Get licenses expiring within specified days with Indian compliance details"""
    from datetime import date, timedelta
    expiry_threshold = date.today() + timedelta(days=days_ahead)
    
    return db.query(models.RegulatoryLicense).filter(
        models.RegulatoryLicense.expiry_date <= expiry_threshold,
        models.RegulatoryLicense.status == 'active'
    ).all()

def update_license_compliance_score(db: Session, license_id: int, compliance_score: int, notes: str = None):
    """Update compliance score for a license"""
    db_license = db.query(models.RegulatoryLicense).filter(models.RegulatoryLicense.license_id == license_id).first()
    if db_license:
        db_license.compliance_score = compliance_score
        if notes:
            db_license.verification_notes = notes
        db_license.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_license)
    return db_license

# ----------------- CDSCO COMPLIANCE -----------------

def create_cdsco_compliance(db: Session, compliance: schemas.CDSCOComplianceCreate):
    """Create CDSCO compliance record"""
    db_compliance = models.CDSCOCompliance(**compliance.model_dump())
    db.add(db_compliance)
    db.commit()
    db.refresh(db_compliance)
    return db_compliance

def get_cdsco_compliance(db: Session, license_id: int = None, form_type: str = None):
    """Get CDSCO compliance records"""
    query = db.query(models.CDSCOCompliance)
    
    if license_id:
        query = query.filter(models.CDSCOCompliance.license_id == license_id)
    if form_type:
        query = query.filter(models.CDSCOCompliance.form_type == form_type)
    
    return query.all()

def update_cdsco_monthly_report(db: Session, compliance_id: int):
    """Update monthly report filing count"""
    db_compliance = db.query(models.CDSCOCompliance).filter(models.CDSCOCompliance.compliance_id == compliance_id).first()
    if db_compliance:
        db_compliance.monthly_reports_filed += 1
        db_compliance.last_monthly_report_date = date.today()
        db_compliance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_compliance)
    return db_compliance

def update_adr_report(db: Session, compliance_id: int):
    """Update ADR report filing count"""
    db_compliance = db.query(models.CDSCOCompliance).filter(models.CDSCOCompliance.compliance_id == compliance_id).first()
    if db_compliance:
        db_compliance.adr_reports_filed += 1
        db_compliance.last_adr_report_date = date.today()
        db_compliance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_compliance)
    return db_compliance

# ----------------- STATE DRUG CONTROLLER COMPLIANCE -----------------

def create_state_compliance(db: Session, compliance: schemas.StateDrugControllerComplianceCreate):
    """Create state drug controller compliance record"""
    db_compliance = models.StateDrugControllerCompliance(**compliance.model_dump())
    db.add(db_compliance)
    db.commit()
    db.refresh(db_compliance)
    return db_compliance

def get_state_compliance(db: Session, license_id: int = None, state: str = None):
    """Get state drug controller compliance records"""
    query = db.query(models.StateDrugControllerCompliance)
    
    if license_id:
        query = query.filter(models.StateDrugControllerCompliance.license_id == license_id)
    if state:
        query = query.filter(models.StateDrugControllerCompliance.state == state)
    
    return query.all()

def update_inspection_record(db: Session, compliance_id: int, inspection_result: str, inspector_name: str, notes: str = None):
    """Update inspection record"""
    db_compliance = db.query(models.StateDrugControllerCompliance).filter(
        models.StateDrugControllerCompliance.compliance_id == compliance_id
    ).first()
    
    if db_compliance:
        db_compliance.last_inspection_date = date.today()
        db_compliance.inspection_result = inspection_result
        db_compliance.inspector_name = inspector_name
        
        # Set compliance status based on inspection result
        if inspection_result == 'satisfactory':
            db_compliance.current_status = 'compliant'
        elif inspection_result == 'needs_improvement':
            db_compliance.current_status = 'warning'
        else:
            db_compliance.current_status = 'violation'
        
        # Calculate next inspection date (typically 1 year)
        from datetime import timedelta
        db_compliance.next_inspection_due = date.today() + timedelta(days=365)
        
        db_compliance.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_compliance)
    
    return db_compliance

# ----------------- LICENSE DOCUMENT MANAGEMENT -----------------

def create_license_document(db: Session, document: schemas.LicenseDocumentCreate):
    """Create license document record"""
    db_document = models.LicenseDocument(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_license_documents(db: Session, license_id: int, document_type: str = None):
    """Get documents for a specific license"""
    query = db.query(models.LicenseDocument).filter(models.LicenseDocument.license_id == license_id)
    
    if document_type:
        query = query.filter(models.LicenseDocument.document_type == document_type)
    
    return query.order_by(models.LicenseDocument.upload_date.desc()).all()

def verify_license_document(db: Session, document_id: int, verified_by: int, status: str, notes: str = None):
    """Verify or reject a license document"""
    db_document = db.query(models.LicenseDocument).filter(models.LicenseDocument.document_id == document_id).first()
    
    if db_document:
        db_document.verification_status = status
        db_document.verified_by = verified_by
        db_document.verification_date = datetime.utcnow()
        if notes:
            db_document.verification_notes = notes
        
        # Update the main license verification status
        if status == 'verified':
            license = db.query(models.RegulatoryLicense).filter(
                models.RegulatoryLicense.license_id == db_document.license_id
            ).first()
            if license:
                license.document_verification_status = 'verified'
                license.verified_by = verified_by
                license.verification_date = date.today()
        
        db.commit()
        db.refresh(db_document)
    
    return db_document

def get_pending_document_verifications(db: Session, limit: int = 50):
    """Get documents pending verification"""
    return db.query(models.LicenseDocument).filter(
        models.LicenseDocument.verification_status == 'pending'
    ).limit(limit).all()

# ----------------- COMPLIANCE DASHBOARD -----------------

def get_compliance_dashboard(db: Session) -> schemas.ComplianceDashboard:
    """Get compliance dashboard data"""
    from datetime import date, timedelta
    
    # License statistics
    total_licenses = db.query(models.RegulatoryLicense).count()
    active_licenses = db.query(models.RegulatoryLicense).filter(models.RegulatoryLicense.status == 'active').count()
    
    expiry_threshold = date.today() + timedelta(days=60)
    expiring_soon = db.query(models.RegulatoryLicense).filter(
        models.RegulatoryLicense.expiry_date <= expiry_threshold,
        models.RegulatoryLicense.status == 'active'
    ).count()
    
    expired_licenses = db.query(models.RegulatoryLicense).filter(
        models.RegulatoryLicense.expiry_date < date.today(),
        models.RegulatoryLicense.status == 'active'
    ).count()
    
    pending_renewals = db.query(models.RegulatoryLicense).filter(
        models.RegulatoryLicense.renewal_due_date <= date.today(),
        models.RegulatoryLicense.status == 'active'
    ).count()
    
    # CDSCO statistics
    cdsco_forms_pending = db.query(models.CDSCOCompliance).filter(
        models.CDSCOCompliance.status.in_(['submitted', 'pending'])
    ).count()
    
    # Count ADR reports pending (monthly reports filed < monthly reports due)
    adr_reports_pending = db.query(models.CDSCOCompliance).filter(
        models.CDSCOCompliance.adr_reports_filed < 1  # Assuming at least 1 ADR report should be filed
    ).count()
    
    monthly_reports_pending = db.query(models.CDSCOCompliance).filter(
        models.CDSCOCompliance.monthly_reports_filed < models.CDSCOCompliance.monthly_reports_due
    ).count()
    
    # State compliance statistics
    states_covered = db.query(models.StateDrugControllerCompliance.state).distinct().count()
    
    inspection_due_count = db.query(models.StateDrugControllerCompliance).filter(
        models.StateDrugControllerCompliance.next_inspection_due <= date.today()
    ).count()
    
    compliance_violations = db.query(models.StateDrugControllerCompliance).filter(
        models.StateDrugControllerCompliance.current_status == 'violation'
    ).count()
    
    # Document statistics
    documents_pending_verification = db.query(models.LicenseDocument).filter(
        models.LicenseDocument.verification_status == 'pending'
    ).count()
    
    documents_verified = db.query(models.LicenseDocument).filter(
        models.LicenseDocument.verification_status == 'verified'
    ).count()
    
    documents_rejected = db.query(models.LicenseDocument).filter(
        models.LicenseDocument.verification_status == 'rejected'
    ).count()
    
    return schemas.ComplianceDashboard(
        total_licenses=total_licenses,
        active_licenses=active_licenses,
        expiring_soon=expiring_soon,
        expired_licenses=expired_licenses,
        pending_renewals=pending_renewals,
        cdsco_forms_pending=cdsco_forms_pending,
        adr_reports_pending=adr_reports_pending,
        monthly_reports_pending=monthly_reports_pending,
        states_covered=states_covered,
        inspection_due_count=inspection_due_count,
        compliance_violations=compliance_violations,
        documents_pending_verification=documents_pending_verification,
        documents_verified=documents_verified,
        documents_rejected=documents_rejected
    )

# ====================== FILE UPLOAD OPERATIONS ======================
def upload_file(db: Session, file_data: dict, user_id: int):
    """Handle file upload with metadata tracking"""
    try:
        from .models import FileUpload
        
        file_upload = FileUpload(
            original_filename=file_data['original_filename'],
            stored_filename=file_data['stored_filename'],
            file_path=file_data['file_path'],
            file_size=file_data['file_size'],
            file_type=file_data['file_type'],
            file_extension=file_data.get('file_extension'),
            uploaded_by=user_id,
            upload_purpose=file_data['upload_purpose'],
            entity_type=file_data['entity_type'],
            entity_id=file_data['entity_id'],
            description=file_data.get('description'),
            tags=json.dumps(file_data.get('tags', [])),
            is_temporary=file_data.get('is_temporary', False),
            access_level=file_data.get('access_level', 'private')
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        return file_upload
    except Exception as e:
        db.rollback()
        raise Exception(f"File upload failed: {str(e)}")

def get_file_by_id(db: Session, file_id: int):
    """Get file upload record by ID"""
    from .models import FileUpload
    return db.query(FileUpload).filter(FileUpload.file_id == file_id).first()

def verify_file_upload(db: Session, file_id: int, user_id: int, status: str, notes: str = None):
    """Verify uploaded file"""
    try:
        from .models import FileUpload
        
        file_upload = get_file_by_id(db, file_id)
        if not file_upload:
            raise Exception("File not found")
        
        file_upload.verification_status = status
        file_upload.verified_by = user_id
        file_upload.verification_date = datetime.utcnow()
        file_upload.verification_notes = notes
        file_upload.is_verified = (status == 'verified')
        
        db.commit()
        db.refresh(file_upload)
        
        return file_upload
    except Exception as e:
        db.rollback()
        raise Exception(f"File verification failed: {str(e)}")

def get_files_by_entity(db: Session, entity_type: str, entity_id: int):
    """Get all files for a specific entity"""
    from .models import FileUpload
    return db.query(FileUpload).filter(
        FileUpload.entity_type == entity_type,
        FileUpload.entity_id == entity_id
    ).all()

# ====================== LOYALTY PROGRAM OPERATIONS ======================
def create_loyalty_program(db: Session, program_data: dict):
    """Create a new loyalty program"""
    try:
        from .models import LoyaltyProgram
        
        program = LoyaltyProgram(**program_data)
        db.add(program)
        db.commit()
        db.refresh(program)
        
        return program
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to create loyalty program: {str(e)}")

def get_loyalty_program(db: Session, program_id: int):
    """Get loyalty program by ID"""
    from .models import LoyaltyProgram
    return db.query(LoyaltyProgram).filter(LoyaltyProgram.program_id == program_id).first()

def get_active_loyalty_programs(db: Session):
    """Get all active loyalty programs"""
    from .models import LoyaltyProgram
    return db.query(LoyaltyProgram).filter(LoyaltyProgram.is_active == True).all()

def enroll_customer_in_loyalty(db: Session, customer_id: int, program_id: int):
    """Enroll customer in loyalty program"""
    try:
        from .models import CustomerLoyalty, LoyaltyProgram
        
        # Check if already enrolled
        existing = db.query(CustomerLoyalty).filter(
            CustomerLoyalty.customer_id == customer_id,
            CustomerLoyalty.program_id == program_id
        ).first()
        
        if existing:
            raise Exception("Customer already enrolled in this program")
        
        # Get program details for signup bonus
        program = get_loyalty_program(db, program_id)
        if not program:
            raise Exception("Loyalty program not found")
        
        # Create loyalty record
        customer_loyalty = CustomerLoyalty(
            customer_id=customer_id,
            program_id=program_id,
            current_points=program.signup_bonus_points,
            lifetime_points_earned=program.signup_bonus_points
        )
        
        db.add(customer_loyalty)
        
        # Add signup bonus transaction if applicable
        if program.signup_bonus_points > 0:
            signup_transaction = create_loyalty_transaction(
                db=db,
                transaction_data={
                    'customer_id': customer_id,
                    'program_id': program_id,
                    'transaction_type': 'bonus',
                    'points': program.signup_bonus_points,
                    'transaction_reason': 'signup_bonus',
                    'points_before': 0,
                    'points_after': program.signup_bonus_points
                }
            )
        
        db.commit()
        db.refresh(customer_loyalty)
        
        return customer_loyalty
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to enroll customer: {str(e)}")

def get_customer_loyalty(db: Session, customer_id: int, program_id: int = None):
    """Get customer loyalty information"""
    from .models import CustomerLoyalty
    
    query = db.query(CustomerLoyalty).filter(CustomerLoyalty.customer_id == customer_id)
    if program_id:
        query = query.filter(CustomerLoyalty.program_id == program_id)
    
    if program_id:
        return query.first()
    return query.all()

def create_loyalty_transaction(db: Session, transaction_data: dict):
    """Create loyalty transaction"""
    try:
        from .models import LoyaltyTransaction
        
        transaction = LoyaltyTransaction(**transaction_data)
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to create loyalty transaction: {str(e)}")

def award_loyalty_points(db: Session, customer_id: int, program_id: int, order_amount: float, order_id: int = None):
    """Award loyalty points for purchase"""
    try:
        from .models import CustomerLoyalty, LoyaltyProgram
        
        # Get program and customer loyalty
        program = get_loyalty_program(db, program_id)
        customer_loyalty = get_customer_loyalty(db, customer_id, program_id)
        
        if not program or not customer_loyalty:
            raise Exception("Program or customer loyalty record not found")
        
        # Check minimum order value
        if order_amount < program.min_order_value_for_points:
            return None
        
        # Calculate points
        points_to_award = int(order_amount * program.points_per_rupee)
        
        # Apply cap if set
        if program.max_points_per_transaction and points_to_award > program.max_points_per_transaction:
            points_to_award = program.max_points_per_transaction
        
        # Update customer loyalty
        points_before = customer_loyalty.current_points
        customer_loyalty.current_points += points_to_award
        customer_loyalty.lifetime_points_earned += points_to_award
        customer_loyalty.last_activity_date = datetime.utcnow().date()
        
        # Create transaction record
        transaction = create_loyalty_transaction(
            db=db,
            transaction_data={
                'customer_id': customer_id,
                'program_id': program_id,
                'transaction_type': 'earned',
                'points': points_to_award,
                'order_id': order_id,
                'transaction_reason': 'purchase',
                'order_amount': order_amount,
                'points_before': points_before,
                'points_after': customer_loyalty.current_points,
                'points_expiry_date': datetime.utcnow().date() + timedelta(days=30*program.points_expiry_months)
            }
        )
        
        db.commit()
        return transaction
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to award loyalty points: {str(e)}")

def redeem_loyalty_points(db: Session, customer_id: int, program_id: int, points_to_redeem: int, order_id: int = None):
    """Redeem loyalty points"""
    try:
        from .models import CustomerLoyalty, LoyaltyProgram, LoyaltyRedemption
        
        # Get program and customer loyalty
        program = get_loyalty_program(db, program_id)
        customer_loyalty = get_customer_loyalty(db, customer_id, program_id)
        
        if not program or not customer_loyalty:
            raise Exception("Program or customer loyalty record not found")
        
        # Validate redemption
        if points_to_redeem < program.minimum_redemption_points:
            raise Exception(f"Minimum redemption is {program.minimum_redemption_points} points")
        
        if program.maximum_redemption_points and points_to_redeem > program.maximum_redemption_points:
            raise Exception(f"Maximum redemption is {program.maximum_redemption_points} points")
        
        if customer_loyalty.current_points < points_to_redeem:
            raise Exception("Insufficient points")
        
        # Calculate cash value
        cash_value = points_to_redeem * program.points_redemption_value
        
        # Update customer loyalty
        points_before = customer_loyalty.current_points
        customer_loyalty.current_points -= points_to_redeem
        customer_loyalty.lifetime_points_redeemed += points_to_redeem
        customer_loyalty.last_activity_date = datetime.utcnow().date()
        
        # Create redemption record
        redemption = LoyaltyRedemption(
            customer_id=customer_id,
            order_id=order_id,
            points_redeemed=points_to_redeem,
            cash_value=cash_value
        )
        db.add(redemption)
        
        # Create transaction record
        transaction = create_loyalty_transaction(
            db=db,
            transaction_data={
                'customer_id': customer_id,
                'program_id': program_id,
                'transaction_type': 'redeemed',
                'points': -points_to_redeem,  # Negative for redemption
                'order_id': order_id,
                'transaction_reason': 'redemption',
                'redemption_amount': cash_value,
                'points_before': points_before,
                'points_after': customer_loyalty.current_points
            }
        )
        
        db.commit()
        db.refresh(redemption)
        
        return {'redemption': redemption, 'cash_value': cash_value}
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to redeem points: {str(e)}")

# ====================== UPI PAYMENT OPERATIONS ======================
def generate_upi_qr_code(db: Session, payment_data: dict):
    """Generate UPI QR code for payment"""
    try:
        import uuid
        from .models import UPIPayment
        
        # Generate unique merchant transaction ID
        merchant_tx_id = f"PHR{uuid.uuid4().hex[:12].upper()}"
        
        # UPI payment string format
        # upi://pay?pa=merchant@upi&pn=MerchantName&am=amount&tn=description&tr=transaction_id
        upi_id = "pharmacy@hdfc"  # Your UPI ID
        merchant_name = "Pharma Wholesale Ltd"
        amount = payment_data['amount']
        description = f"Order Payment - {payment_data.get('order_id', 'Advance')}"
        
        qr_string = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn={description}&tr={merchant_tx_id}"
        
        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(minutes=payment_data.get('expires_in_minutes', 15))
        
        # Create UPI payment record
        upi_payment = UPIPayment(
            order_id=payment_data.get('order_id'),
            customer_id=payment_data['customer_id'],
            amount=amount,
            upi_id=payment_data.get('upi_id'),
            qr_code_string=qr_string,
            merchant_transaction_id=merchant_tx_id,
            expires_at=expires_at
        )
        
        db.add(upi_payment)
        db.commit()
        db.refresh(upi_payment)
        
        return upi_payment
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to generate UPI QR code: {str(e)}")

def update_upi_payment_status(db: Session, merchant_tx_id: str, status_data: dict):
    """Update UPI payment status"""
    try:
        from .models import UPIPayment
        
        upi_payment = db.query(UPIPayment).filter(
            UPIPayment.merchant_transaction_id == merchant_tx_id
        ).first()
        
        if not upi_payment:
            raise Exception("UPI payment record not found")
        
        # Update payment details
        upi_payment.payment_status = status_data['payment_status']
        upi_payment.upi_transaction_id = status_data.get('upi_transaction_id')
        upi_payment.amount_received = status_data.get('amount_received')
        upi_payment.payer_bank = status_data.get('payer_bank')
        upi_payment.bank_reference_number = status_data.get('bank_reference_number')
        upi_payment.fees_deducted = status_data.get('fees_deducted', 0)
        
        if status_data['payment_status'] == 'completed':
            upi_payment.completed_at = datetime.utcnow()
            upi_payment.settlement_amount = upi_payment.amount_received - upi_payment.fees_deducted
        
        db.commit()
        db.refresh(upi_payment)
        
        return upi_payment
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to update UPI payment status: {str(e)}")

def get_upi_payment_by_merchant_id(db: Session, merchant_tx_id: str):
    """Get UPI payment by merchant transaction ID"""
    from .models import UPIPayment
    return db.query(UPIPayment).filter(
        UPIPayment.merchant_transaction_id == merchant_tx_id
    ).first()

def get_customer_upi_payments(db: Session, customer_id: int, status: str = None):
    """Get customer's UPI payments"""
    from .models import UPIPayment
    
    query = db.query(UPIPayment).filter(UPIPayment.customer_id == customer_id)
    if status:
        query = query.filter(UPIPayment.payment_status == status)
    
    return query.order_by(UPIPayment.initiated_at.desc()).all()

def reconcile_upi_payment(db: Session, upi_payment_id: int, user_id: int, bank_matched: bool = True):
    """Reconcile UPI payment with bank statement"""
    try:
        from .models import UPIPayment
        
        upi_payment = db.query(UPIPayment).filter(
            UPIPayment.upi_payment_id == upi_payment_id
        ).first()
        
        if not upi_payment:
            raise Exception("UPI payment not found")
        
        upi_payment.bank_statement_matched = bank_matched
        upi_payment.reconciliation_status = 'matched' if bank_matched else 'disputed'
        upi_payment.reconciled_by = user_id
        upi_payment.reconciliation_date = datetime.utcnow()
        
        db.commit()
        db.refresh(upi_payment)
        
        return upi_payment
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to reconcile UPI payment: {str(e)}")


# ----------------- CRUD INSTANCES USING CRUD BASE -----------------
# FIXED: Added missing CRUD instances that were causing import errors
# These instances use the generic CRUD base class for common operations
# Import the crud base
try:
    from .core.crud_base import create_crud
except ImportError:
    try:
        from core.crud_base import create_crud
    except ImportError:
        # Try absolute import if relative fails
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from core.crud_base import create_crud

# Create CRUD instances for models that use the generic CRUD
challan_crud = create_crud(models.Challan)
challan_item_crud = create_crud(models.ChallanItem)
customer_crud = create_crud(models.Customer)
product_crud = create_crud(models.Product)
order_crud = create_crud(models.Order)
batch_crud = create_crud(models.Batch)
