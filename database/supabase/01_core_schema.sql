-- =============================================
-- PHARMACEUTICAL ERP - PRODUCTION CORE SCHEMA
-- =============================================
-- Version: 1.0 - Production Ready
-- Description: Complete pharmaceutical ERP schema
-- Deploy Order: 1st - Core tables and structure
-- =============================================

-- =============================================
-- EXTENSIONS
-- =============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- ORGANIZATIONS & MULTI-TENANCY
-- =============================================

-- Main organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_name TEXT NOT NULL,
    business_type TEXT DEFAULT 'pharmaceutical',
    
    -- Business identification
    company_registration_number TEXT,
    pan_number TEXT,
    gst_number TEXT UNIQUE,
    drug_license_number TEXT,
    
    -- Contact information
    primary_contact_name TEXT,
    primary_email TEXT,
    primary_phone TEXT,
    business_address JSONB,
    
    -- Subscription details
    plan_type TEXT DEFAULT 'starter',
    subscription_status TEXT DEFAULT 'active',
    subscription_start_date DATE DEFAULT CURRENT_DATE,
    subscription_end_date DATE,
    
    -- Feature limits
    max_users INTEGER DEFAULT 5,
    max_products INTEGER DEFAULT 1000,
    max_customers INTEGER DEFAULT 500,
    max_monthly_transactions INTEGER DEFAULT 1000,
    
    -- Settings
    business_settings JSONB DEFAULT '{}',
    features_enabled TEXT[] DEFAULT ARRAY['basic_erp'],
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Organization users
CREATE TABLE IF NOT EXISTS org_users (
    user_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- User details
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    employee_id TEXT,
    
    -- Authentication
    password_hash TEXT NOT NULL,
    auth_method TEXT DEFAULT 'password',
    
    -- Role and permissions
    role TEXT NOT NULL,
    permissions JSONB DEFAULT '{}',
    
    -- Access control
    department TEXT,
    branch_access INTEGER[],
    can_view_reports BOOLEAN DEFAULT FALSE,
    can_modify_prices BOOLEAN DEFAULT FALSE,
    can_approve_discounts BOOLEAN DEFAULT FALSE,
    discount_limit_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Session management
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, email)
);

-- Organization branches
CREATE TABLE IF NOT EXISTS org_branches (
    branch_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Branch details
    branch_name TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    branch_type TEXT DEFAULT 'retail',
    
    -- Contact information
    address JSONB NOT NULL,
    phone TEXT,
    email TEXT,
    
    -- Manager
    branch_manager_id INTEGER REFERENCES org_users(user_id),
    
    -- Settings
    branch_settings JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, branch_code)
);

-- =============================================
-- PRODUCT MANAGEMENT
-- =============================================

-- Product types (system + custom)
CREATE TABLE IF NOT EXISTS product_types (
    type_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    type_code TEXT NOT NULL,
    type_name TEXT NOT NULL,
    form_category TEXT NOT NULL,
    default_base_uom TEXT,
    default_purchase_uom TEXT,
    default_display_uom TEXT,
    storage_conditions TEXT[],
    requires_refrigeration BOOLEAN DEFAULT FALSE,
    is_schedule_h BOOLEAN DEFAULT FALSE,
    is_narcotic BOOLEAN DEFAULT FALSE,
    is_system_defined BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, type_code)
);

-- Units of measure
CREATE TABLE IF NOT EXISTS units_of_measure (
    uom_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    uom_code TEXT NOT NULL,
    uom_name TEXT NOT NULL,
    uom_category TEXT NOT NULL,
    base_unit BOOLEAN DEFAULT FALSE,
    is_fractional BOOLEAN DEFAULT FALSE,
    decimal_places INTEGER DEFAULT 0,
    is_system_defined BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, uom_code)
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    category_name TEXT NOT NULL,
    parent_category_id INTEGER REFERENCES categories(category_id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_system_defined BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, category_name)
);

-- Products master
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Product identification
    product_code TEXT NOT NULL,
    product_name TEXT NOT NULL,
    generic_name TEXT,
    brand_name TEXT,
    manufacturer TEXT,
    manufacturer_code TEXT,
    
    -- Classification
    category TEXT,
    subcategory TEXT,
    category_id INTEGER REFERENCES categories(category_id),
    product_type_id INTEGER REFERENCES product_types(type_id),
    
    -- Multi-UOM fields
    base_uom_code TEXT DEFAULT 'PIECE',
    purchase_uom_code TEXT,
    sale_uom_code TEXT,
    display_uom_code TEXT,
    allow_loose_units BOOLEAN DEFAULT FALSE,
    
    -- Regulatory
    hsn_code TEXT,
    drug_schedule TEXT,
    prescription_required BOOLEAN DEFAULT FALSE,
    is_controlled_substance BOOLEAN DEFAULT FALSE,
    
    -- Pricing
    purchase_price DECIMAL(12,2) DEFAULT 0,
    sale_price DECIMAL(12,2) DEFAULT 0,
    mrp DECIMAL(12,2) DEFAULT 0,
    trade_discount_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Tax
    gst_percent DECIMAL(5,2) DEFAULT 12,
    cgst_percent DECIMAL(5,2) DEFAULT 6,
    sgst_percent DECIMAL(5,2) DEFAULT 6,
    igst_percent DECIMAL(5,2) DEFAULT 12,
    tax_category TEXT DEFAULT 'standard',
    
    -- Inventory
    minimum_stock_level INTEGER DEFAULT 0,
    maximum_stock_level INTEGER,
    reorder_level INTEGER,
    reorder_quantity INTEGER,
    
    -- Packaging
    pack_size TEXT,
    pack_details JSONB,
    
    -- Barcodes
    barcode TEXT UNIQUE,
    barcode_type TEXT DEFAULT 'EAN13',
    alternate_barcodes TEXT[],
    
    -- Additional fields
    storage_location TEXT,
    shelf_life_days INTEGER,
    notes TEXT,
    tags TEXT[],
    
    -- Search optimization
    search_keywords TEXT[],
    category_path TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_discontinued BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, product_code)
);

-- Product UOM conversions
CREATE TABLE IF NOT EXISTS product_uom_conversions (
    conversion_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    
    -- Conversion details
    from_uom_code TEXT NOT NULL,
    from_quantity DECIMAL(10,3) NOT NULL DEFAULT 1,
    to_uom_code TEXT NOT NULL,
    to_quantity DECIMAL(10,3) NOT NULL,
    
    -- Settings
    is_default BOOLEAN DEFAULT FALSE,
    allow_fraction_sale BOOLEAN DEFAULT FALSE,
    round_to_nearest DECIMAL(10,3),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(product_id, from_uom_code, to_uom_code)
);

-- =============================================
-- CUSTOMER & SUPPLIER MANAGEMENT
-- =============================================

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Customer identification
    customer_code TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_type TEXT DEFAULT 'retail',
    business_type TEXT,
    
    -- Contact information
    phone TEXT,
    alternate_phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    pincode TEXT,
    landmark TEXT,
    
    -- Regulatory
    gst_number TEXT,
    pan_number TEXT,
    drug_license_number TEXT,
    food_license_number TEXT,
    
    -- Credit management
    credit_limit DECIMAL(12,2) DEFAULT 0,
    credit_period_days INTEGER DEFAULT 0,
    payment_terms TEXT,
    
    -- Pricing
    price_list_id INTEGER,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Relationship
    assigned_sales_rep INTEGER REFERENCES org_users(user_id),
    customer_group TEXT,
    loyalty_points INTEGER DEFAULT 0,
    
    -- Business metrics
    total_business DECIMAL(15,2) DEFAULT 0,
    outstanding_amount DECIMAL(12,2) DEFAULT 0,
    last_order_date DATE,
    order_count INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    blacklisted BOOLEAN DEFAULT FALSE,
    blacklist_reason TEXT,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, customer_code)
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Supplier identification
    supplier_code TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    company_name TEXT,
    supplier_type TEXT DEFAULT 'manufacturer',
    
    -- Contact information
    contact_person TEXT,
    phone TEXT,
    alternate_phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    pincode TEXT,
    
    -- Regulatory
    gst_number TEXT,
    pan_number TEXT,
    drug_license_number TEXT,
    
    -- Payment terms
    credit_period_days INTEGER DEFAULT 30,
    payment_terms TEXT,
    payment_method TEXT,
    
    -- Banking
    bank_name TEXT,
    account_number TEXT,
    ifsc_code TEXT,
    
    -- Business metrics
    total_purchases DECIMAL(15,2) DEFAULT 0,
    outstanding_amount DECIMAL(12,2) DEFAULT 0,
    last_purchase_date DATE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    rating INTEGER,
    notes TEXT,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, supplier_code)
);

-- =============================================
-- INVENTORY MANAGEMENT
-- =============================================

-- Product batches
CREATE TABLE IF NOT EXISTS batches (
    batch_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    
    -- Batch identification
    batch_number TEXT NOT NULL,
    lot_number TEXT,
    serial_number TEXT,
    
    -- Dates
    manufacturing_date DATE,
    expiry_date DATE NOT NULL,
    days_to_expiry INTEGER,
    is_near_expiry BOOLEAN DEFAULT FALSE,
    
    -- Quantities
    quantity_received INTEGER NOT NULL,
    quantity_available INTEGER NOT NULL,
    quantity_sold INTEGER DEFAULT 0,
    quantity_damaged INTEGER DEFAULT 0,
    quantity_returned INTEGER DEFAULT 0,
    
    -- UOM tracking
    received_uom TEXT,
    base_quantity INTEGER,
    
    -- Pricing
    cost_price DECIMAL(12,2),
    selling_price DECIMAL(12,2),
    mrp DECIMAL(12,2),
    
    -- Source
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    purchase_id INTEGER,
    purchase_invoice_number TEXT,
    
    -- Location
    branch_id INTEGER REFERENCES org_branches(branch_id),
    location_code TEXT,
    rack_number TEXT,
    
    -- Status
    batch_status TEXT DEFAULT 'active',
    is_blocked BOOLEAN DEFAULT FALSE,
    block_reason TEXT,
    current_stock_status TEXT,
    
    -- Metadata
    notes TEXT,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, product_id, batch_number)
);

-- Inventory movements
CREATE TABLE IF NOT EXISTS inventory_movements (
    movement_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Movement details
    movement_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    movement_type TEXT NOT NULL,
    
    -- Product and batch
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    batch_id INTEGER REFERENCES batches(batch_id),
    
    -- Quantities
    quantity_in INTEGER DEFAULT 0,
    quantity_out INTEGER DEFAULT 0,
    balance_quantity INTEGER,
    
    -- UOM tracking
    movement_uom TEXT,
    base_quantity_in INTEGER DEFAULT 0,
    base_quantity_out INTEGER DEFAULT 0,
    
    -- Reference
    reference_type TEXT,
    reference_id INTEGER,
    reference_number TEXT,
    
    -- Location
    branch_id INTEGER REFERENCES org_branches(branch_id),
    from_location TEXT,
    to_location TEXT,
    
    -- User and notes
    performed_by INTEGER REFERENCES org_users(user_id),
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ORDERS & TRANSACTIONS
-- =============================================

-- Sales orders
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Order identification
    order_number TEXT NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    order_time TIME DEFAULT CURRENT_TIME,
    
    -- Customer
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    customer_name TEXT,
    customer_phone TEXT,
    
    -- Amounts
    subtotal_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    round_off_amount DECIMAL(5,2) DEFAULT 0,
    final_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Payment
    payment_mode TEXT DEFAULT 'cash',
    payment_status TEXT DEFAULT 'pending',
    paid_amount DECIMAL(12,2) DEFAULT 0,
    balance_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Invoice
    invoice_number TEXT,
    invoice_date DATE,
    payment_due_date DATE,
    
    -- Delivery
    delivery_type TEXT DEFAULT 'pickup',
    delivery_address TEXT,
    delivery_status TEXT DEFAULT 'pending',
    delivered_date DATE,
    
    -- Status
    order_status TEXT DEFAULT 'pending',
    
    -- Branch and user
    branch_id INTEGER REFERENCES org_branches(branch_id),
    created_by INTEGER REFERENCES org_users(user_id),
    approved_by INTEGER REFERENCES org_users(user_id),
    
    -- Metadata
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, order_number)
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    
    -- Product details
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    product_name TEXT,
    
    -- Batch allocation
    batch_id INTEGER REFERENCES batches(batch_id),
    batch_number TEXT,
    expiry_date DATE,
    
    -- Quantities
    quantity INTEGER NOT NULL,
    uom_code TEXT,
    base_quantity INTEGER,
    
    -- Pricing
    mrp DECIMAL(12,2),
    selling_price DECIMAL(12,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Tax
    tax_percent DECIMAL(5,2),
    tax_amount DECIMAL(12,2),
    
    -- Totals
    total_price DECIMAL(12,2) NOT NULL,
    
    -- Status
    item_status TEXT DEFAULT 'active',
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Purchase orders
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Purchase identification
    purchase_number TEXT NOT NULL,
    purchase_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Supplier
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    supplier_name TEXT,
    supplier_invoice_number TEXT,
    supplier_invoice_date DATE,
    
    -- Amounts
    subtotal_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    other_charges DECIMAL(12,2) DEFAULT 0,
    final_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Payment
    payment_status TEXT DEFAULT 'pending',
    paid_amount DECIMAL(12,2) DEFAULT 0,
    payment_due_date DATE,
    
    -- Status
    purchase_status TEXT DEFAULT 'draft',
    grn_number TEXT,
    grn_date DATE,
    
    -- Branch and user
    branch_id INTEGER REFERENCES org_branches(branch_id),
    created_by INTEGER REFERENCES org_users(user_id),
    approved_by INTEGER REFERENCES org_users(user_id),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, purchase_number)
);

-- Purchase items
CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL REFERENCES purchases(purchase_id) ON DELETE CASCADE,
    
    -- Product details
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    product_name TEXT,
    
    -- Quantities
    ordered_quantity INTEGER NOT NULL,
    received_quantity INTEGER DEFAULT 0,
    free_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    
    -- UOM
    purchase_uom TEXT,
    base_quantity INTEGER,
    
    -- Pricing
    cost_price DECIMAL(12,2) NOT NULL,
    mrp DECIMAL(12,2),
    
    -- Discount
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Tax
    tax_percent DECIMAL(5,2),
    tax_amount DECIMAL(12,2),
    
    -- Totals
    total_price DECIMAL(12,2) NOT NULL,
    
    -- Batch details
    batch_number TEXT,
    manufacturing_date DATE,
    expiry_date DATE,
    
    -- Status
    item_status TEXT DEFAULT 'pending',
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- PAYMENTS & OUTSTANDING
-- =============================================

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Payment identification
    payment_number TEXT NOT NULL,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Party details
    customer_id INTEGER REFERENCES customers(customer_id),
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    payment_type TEXT NOT NULL, -- 'receipt' or 'payment'
    
    -- Amount
    amount DECIMAL(12,2) NOT NULL,
    
    -- Payment details
    payment_mode TEXT NOT NULL,
    reference_number TEXT,
    bank_name TEXT,
    
    -- Status
    payment_status TEXT DEFAULT 'pending',
    cleared_date DATE,
    
    -- Branch and user
    branch_id INTEGER REFERENCES org_branches(branch_id),
    created_by INTEGER REFERENCES org_users(user_id),
    approved_by INTEGER REFERENCES org_users(user_id),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, payment_number)
);

-- Customer outstanding
CREATE TABLE IF NOT EXISTS customer_outstanding (
    outstanding_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Customer
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    
    -- Reference
    order_id INTEGER REFERENCES orders(order_id),
    invoice_number TEXT,
    invoice_date DATE NOT NULL,
    
    -- Amounts
    total_amount DECIMAL(12,2) NOT NULL,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    outstanding_amount DECIMAL(12,2) NOT NULL,
    
    -- Due date
    due_date DATE NOT NULL,
    days_overdue INTEGER DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'pending',
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Supplier outstanding
CREATE TABLE IF NOT EXISTS supplier_outstanding (
    outstanding_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    
    -- Supplier
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    
    -- Reference
    purchase_id INTEGER REFERENCES purchases(purchase_id),
    invoice_number TEXT,
    invoice_date DATE NOT NULL,
    
    -- Amounts
    total_amount DECIMAL(12,2) NOT NULL,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    outstanding_amount DECIMAL(12,2) NOT NULL,
    
    -- Due date
    due_date DATE NOT NULL,
    days_overdue INTEGER DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'pending',
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- BARCODE MANAGEMENT
-- =============================================

-- Barcode master
CREATE TABLE IF NOT EXISTS barcode_master (
    barcode_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Barcode details
    barcode_value TEXT NOT NULL UNIQUE,
    barcode_type TEXT NOT NULL DEFAULT 'GTIN',
    
    -- Reference
    reference_type TEXT NOT NULL, -- 'product', 'batch', 'serialized'
    product_id INTEGER REFERENCES products(product_id),
    batch_id INTEGER REFERENCES batches(batch_id),
    
    -- Serial tracking
    serial_number TEXT,
    is_serialized BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, barcode_value)
);

-- Barcode sequences
CREATE TABLE IF NOT EXISTS barcode_sequences (
    sequence_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Sequence details
    sequence_type TEXT NOT NULL, -- 'GTIN', 'SSCC', 'custom'
    prefix TEXT NOT NULL,
    current_value BIGINT DEFAULT 1,
    max_value BIGINT,
    
    -- Settings
    check_digit_algorithm TEXT DEFAULT 'mod10',
    zero_padding INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, sequence_type, prefix)
);

-- =============================================
-- FINANCIAL INTEGRATION
-- =============================================

-- Chart of accounts
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    account_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Account details
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    parent_account_id INTEGER REFERENCES chart_of_accounts(account_id),
    
    -- Properties
    is_group BOOLEAN DEFAULT FALSE,
    is_system_account BOOLEAN DEFAULT FALSE,
    can_have_transactions BOOLEAN DEFAULT TRUE,
    
    -- Balance
    opening_balance DECIMAL(15,2) DEFAULT 0,
    current_balance DECIMAL(15,2) DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, account_code)
);

-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    
    -- Entry details
    entry_number TEXT NOT NULL,
    entry_date DATE NOT NULL,
    entry_type TEXT NOT NULL,
    
    -- Reference
    reference_type TEXT,
    reference_id INTEGER,
    reference_number TEXT,
    
    -- Status
    is_posted BOOLEAN DEFAULT FALSE,
    posted_by INTEGER REFERENCES org_users(user_id),
    posted_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    narration TEXT,
    created_by INTEGER REFERENCES org_users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, entry_number)
);

-- Journal entry lines
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    line_id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES journal_entries(entry_id) ON DELETE CASCADE,
    
    -- Account
    account_id INTEGER NOT NULL REFERENCES chart_of_accounts(account_id),
    
    -- Amounts
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    
    -- Reference
    cost_center TEXT,
    
    -- Metadata
    line_narration TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- SYSTEM TABLES
-- =============================================

-- System notifications
CREATE TABLE IF NOT EXISTS system_notifications (
    notification_id SERIAL PRIMARY KEY,
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    
    target_type TEXT NOT NULL,
    target_value TEXT,
    
    priority TEXT DEFAULT 'medium',
    action_required BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- User sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES org_users(user_id),
    
    -- Session details
    session_token TEXT NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    
    -- Validity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    terminated_at TIMESTAMP WITH TIME ZONE,
    termination_reason TEXT
);

-- Activity log
CREATE TABLE IF NOT EXISTS activity_log (
    log_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES organizations(org_id),
    user_id INTEGER REFERENCES org_users(user_id),
    
    -- Activity details
    activity_type TEXT NOT NULL,
    activity_description TEXT NOT NULL,
    
    -- Reference
    table_name TEXT,
    record_id TEXT,
    old_values JSONB,
    new_values JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System settings
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    
    -- Setting details
    setting_key TEXT NOT NULL,
    setting_value JSONB NOT NULL,
    setting_type TEXT NOT NULL,
    
    -- Metadata
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, setting_key)
);

-- Email queue
CREATE TABLE IF NOT EXISTS email_queue (
    email_id SERIAL PRIMARY KEY,
    org_id UUID REFERENCES organizations(org_id),
    
    -- Email details
    to_email TEXT[] NOT NULL,
    cc_email TEXT[],
    bcc_email TEXT[],
    subject TEXT NOT NULL,
    body_html TEXT,
    body_text TEXT,
    
    -- Attachments
    attachments JSONB,
    
    -- Status
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Priority
    priority INTEGER DEFAULT 5,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- SUCCESS MESSAGE
-- =============================================

DO $$
BEGIN
    RAISE NOTICE '
=============================================
CORE SCHEMA DEPLOYED SUCCESSFULLY
=============================================
✓ Organizations & Multi-tenancy
✓ Product Management
✓ Customer & Supplier Management  
✓ Inventory Management
✓ Orders & Transactions
✓ Payments & Outstanding
✓ Barcode Management
✓ Financial Integration
✓ System Tables

Total Tables Created: 40+

Next: Deploy 02_business_functions.sql
';
END $$;