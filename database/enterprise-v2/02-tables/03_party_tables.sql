-- =============================================
-- PARTY MANAGEMENT TABLES
-- =============================================
-- Schema: parties
-- Tables: 8
-- Purpose: Customers, suppliers, and business partners
-- =============================================

-- 1. Customers
CREATE TABLE parties.customers (
    customer_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES master.organizations(org_id) ON DELETE CASCADE,
    
    -- Customer identification
    customer_code TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_type TEXT NOT NULL, -- 'pharmacy', 'hospital', 'clinic', 'institution', 'doctor'
    
    -- Contact information (primary)
    contact_info JSONB NOT NULL DEFAULT '{}',
    -- {
    --   "primary_phone": "9876543210",
    --   "primary_email": "contact@pharmacy.com",
    --   "alternate_phones": ["9876543211"],
    --   "contact_person": "Mr. Sharma",
    --   "contact_person_phone": "9876543212"
    -- }
    
    -- Business information
    business_info JSONB DEFAULT '{}',
    -- {
    --   "gst_number": "27AABCU9603R1ZM",
    --   "pan_number": "AABCU9603R",
    --   "drug_license_number": "DL-123456",
    --   "drug_license_validity": "2025-12-31",
    --   "fssai_number": "12345678901234",
    --   "establishment_year": 2010,
    --   "business_type": "retail_pharmacy"
    -- }
    
    -- Credit and payment terms
    credit_info JSONB DEFAULT '{}',
    -- {
    --   "credit_limit": 500000,
    --   "credit_days": 30,
    --   "credit_rating": "A",
    --   "payment_terms": "Net 30",
    --   "security_deposit": 50000,
    --   "overdue_interest_rate": 18
    -- }
    
    -- Classification
    customer_category TEXT, -- 'vip', 'regular', 'new', 'blacklisted'
    customer_grade TEXT, -- 'A', 'B', 'C', 'D'
    
    -- Geographic information
    territory_id INTEGER,
    route_id INTEGER,
    area_code TEXT,
    
    -- Sales information
    assigned_salesperson_id INTEGER REFERENCES master.org_users(user_id),
    price_list_id INTEGER,
    discount_group_id INTEGER,
    
    -- Compliance
    kyc_status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    kyc_verified_date DATE,
    kyc_documents JSONB DEFAULT '[]',
    
    -- Preferences
    preferred_payment_mode TEXT,
    preferred_delivery_time TEXT,
    communication_preferences JSONB DEFAULT '{}',
    
    -- Business metrics
    first_transaction_date DATE,
    last_transaction_date DATE,
    total_business_amount NUMERIC(15,2) DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    average_order_value NUMERIC(15,2) DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    blacklisted BOOLEAN DEFAULT false,
    blacklist_reason TEXT,
    blacklist_date DATE,
    
    -- Loyalty
    loyalty_points NUMERIC(15,2) DEFAULT 0,
    loyalty_tier TEXT DEFAULT 'bronze', -- 'bronze', 'silver', 'gold', 'platinum'
    
    -- Notes
    internal_notes TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES master.org_users(user_id),
    
    UNIQUE(org_id, customer_code),
    CONSTRAINT valid_customer_gst CHECK (
        business_info->>'gst_number' IS NULL OR 
        (business_info->>'gst_number')::TEXT ~ '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    )
);

-- 2. Suppliers
CREATE TABLE parties.suppliers (
    supplier_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES master.organizations(org_id) ON DELETE CASCADE,
    
    -- Supplier identification
    supplier_code TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_type TEXT NOT NULL, -- 'manufacturer', 'distributor', 'stockist', 'importer', 'trader'
    
    -- Contact information
    contact_info JSONB NOT NULL DEFAULT '{}',
    
    -- Business information
    business_info JSONB DEFAULT '{}',
    -- Similar structure as customers
    
    -- Payment terms
    payment_terms JSONB DEFAULT '{}',
    -- {
    --   "payment_days": 45,
    --   "payment_mode": "bank_transfer",
    --   "early_payment_discount": 2,
    --   "late_payment_penalty": 18
    -- }
    
    -- Classification
    supplier_category TEXT, -- 'preferred', 'regular', 'backup', 'blacklisted'
    supplier_grade TEXT, -- 'A', 'B', 'C', 'D'
    
    -- Product categories supplied
    product_categories TEXT[],
    brand_authorizations TEXT[],
    
    -- Compliance and quality
    compliance_rating TEXT DEFAULT 'good', -- 'excellent', 'good', 'average', 'poor', 'blacklisted'
    quality_rating NUMERIC(3,2), -- 1.00 to 5.00
    delivery_rating NUMERIC(3,2),
    
    -- Documents
    vendor_documents JSONB DEFAULT '[]',
    -- [
    --   {"type": "gst_certificate", "number": "GST123", "valid_until": "2025-12-31", "file_path": "..."},
    --   {"type": "drug_license", "number": "DL456", "valid_until": "2024-12-31", "file_path": "..."}
    -- ]
    
    -- Banking details (for payments)
    bank_details JSONB DEFAULT '{}',
    -- {
    --   "account_name": "ABC Pharma Pvt Ltd",
    --   "account_number": "1234567890",
    --   "bank_name": "HDFC Bank",
    --   "branch": "Mumbai Main",
    --   "ifsc_code": "HDFC0001234"
    -- }
    
    -- Credit terms from supplier
    credit_limit_given NUMERIC(15,2),
    current_outstanding NUMERIC(15,2) DEFAULT 0,
    
    -- Business metrics
    first_purchase_date DATE,
    last_purchase_date DATE,
    total_purchase_amount NUMERIC(15,2) DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,
    average_order_value NUMERIC(15,2) DEFAULT 0,
    
    -- Returns and quality
    return_rate_percentage NUMERIC(5,2) DEFAULT 0,
    quality_issue_count INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT false,
    approved_date DATE,
    approved_by INTEGER REFERENCES master.org_users(user_id),
    
    -- Blacklisting
    blacklisted BOOLEAN DEFAULT false,
    blacklist_reason TEXT,
    blacklist_date DATE,
    
    -- Notes
    internal_notes TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES master.org_users(user_id),
    
    UNIQUE(org_id, supplier_code)
);

-- 3. Customer Contacts
CREATE TABLE parties.customer_contacts (
    contact_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES parties.customers(customer_id) ON DELETE CASCADE,
    
    -- Contact details
    contact_name TEXT NOT NULL,
    designation TEXT,
    department TEXT,
    
    -- Communication
    mobile_number TEXT,
    phone_number TEXT,
    email TEXT,
    
    -- Preferences
    is_primary_contact BOOLEAN DEFAULT false,
    contact_for TEXT[], -- ['orders', 'payments', 'complaints', 'general']
    preferred_contact_time TEXT,
    preferred_language TEXT DEFAULT 'English',
    
    -- Personal details
    date_of_birth DATE,
    anniversary_date DATE,
    
    -- Notes
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Supplier Contacts
CREATE TABLE parties.supplier_contacts (
    contact_id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES parties.suppliers(supplier_id) ON DELETE CASCADE,
    
    -- Contact details (similar to customer contacts)
    contact_name TEXT NOT NULL,
    designation TEXT,
    department TEXT,
    
    -- Communication
    mobile_number TEXT,
    phone_number TEXT,
    email TEXT,
    
    -- Specific roles
    is_primary_contact BOOLEAN DEFAULT false,
    contact_for TEXT[], -- ['orders', 'payments', 'quality', 'logistics']
    
    -- Authority levels
    can_negotiate_prices BOOLEAN DEFAULT false,
    can_approve_returns BOOLEAN DEFAULT false,
    max_discount_authority NUMERIC(5,2),
    
    -- Notes
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Customer Groups
CREATE TABLE parties.customer_groups (
    group_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES master.organizations(org_id) ON DELETE CASCADE,
    
    -- Group definition
    group_code TEXT NOT NULL,
    group_name TEXT NOT NULL,
    group_type TEXT NOT NULL, -- 'territory', 'category', 'price', 'discount', 'custom'
    
    -- Group properties
    parent_group_id INTEGER REFERENCES parties.customer_groups(group_id),
    
    -- Benefits
    discount_percentage NUMERIC(5,2),
    price_list_id INTEGER,
    payment_terms_days INTEGER,
    credit_limit_multiplier NUMERIC(3,2) DEFAULT 1.0,
    
    -- Criteria
    eligibility_criteria JSONB DEFAULT '{}',
    -- {
    --   "minimum_business": 100000,
    --   "minimum_transactions": 12,
    --   "customer_types": ["pharmacy", "hospital"]
    -- }
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, group_code)
);

-- 6. Customer Group Members
CREATE TABLE parties.customer_group_members (
    member_id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES parties.customer_groups(group_id) ON DELETE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES parties.customers(customer_id) ON DELETE CASCADE,
    
    -- Membership details
    joined_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date DATE,
    
    -- Override settings
    override_discount NUMERIC(5,2),
    override_credit_limit NUMERIC(15,2),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES master.org_users(user_id),
    
    UNIQUE(group_id, customer_id)
);

-- 7. Territory Management
CREATE TABLE parties.territories (
    territory_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES master.organizations(org_id) ON DELETE CASCADE,
    
    -- Territory definition
    territory_code TEXT NOT NULL,
    territory_name TEXT NOT NULL,
    territory_type TEXT NOT NULL, -- 'state', 'city', 'area', 'route'
    
    -- Hierarchy
    parent_territory_id INTEGER REFERENCES parties.territories(territory_id),
    territory_path TEXT, -- 'Maharashtra/Mumbai/Andheri'
    
    -- Geographic boundaries
    geographic_data JSONB DEFAULT '{}',
    -- {
    --   "state": "Maharashtra",
    --   "city": "Mumbai",
    --   "pincodes": ["400001", "400002"],
    --   "coordinates": {"lat": 19.0760, "lng": 72.8777}
    -- }
    
    -- Assignment
    territory_manager_id INTEGER REFERENCES master.org_users(user_id),
    sales_team_ids INTEGER[],
    
    -- Targets
    monthly_target NUMERIC(15,2),
    quarterly_target NUMERIC(15,2),
    annual_target NUMERIC(15,2),
    
    -- Performance
    current_month_achievement NUMERIC(15,2) DEFAULT 0,
    current_quarter_achievement NUMERIC(15,2) DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, territory_code)
);

-- 8. Routes (Delivery/Sales routes)
CREATE TABLE parties.routes (
    route_id SERIAL PRIMARY KEY,
    org_id UUID NOT NULL REFERENCES master.organizations(org_id) ON DELETE CASCADE,
    territory_id INTEGER REFERENCES parties.territories(territory_id),
    
    -- Route definition
    route_code TEXT NOT NULL,
    route_name TEXT NOT NULL,
    route_type TEXT NOT NULL, -- 'delivery', 'sales', 'collection'
    
    -- Schedule
    visit_days TEXT[], -- ['Monday', 'Thursday']
    visit_frequency TEXT, -- 'weekly', 'bi-weekly', 'monthly'
    
    -- Assignment
    assigned_to_id INTEGER REFERENCES master.org_users(user_id),
    vehicle_required BOOLEAN DEFAULT false,
    
    -- Route optimization
    total_distance_km NUMERIC(10,2),
    average_time_hours NUMERIC(5,2),
    customer_count INTEGER DEFAULT 0,
    
    -- Sequence (for route optimization)
    customer_sequence JSONB DEFAULT '[]',
    -- [
    --   {"sequence": 1, "customer_id": 123, "average_time_minutes": 15},
    --   {"sequence": 2, "customer_id": 124, "average_time_minutes": 20}
    -- ]
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, route_code)
);

-- Create indexes for performance
CREATE INDEX idx_customers_org ON parties.customers(org_id);
CREATE INDEX idx_customers_type ON parties.customers(customer_type);
CREATE INDEX idx_customers_active ON parties.customers(is_active) WHERE is_active = true;
CREATE INDEX idx_customers_gst ON parties.customers((business_info->>'gst_number'));
CREATE INDEX idx_suppliers_org ON parties.suppliers(org_id);
CREATE INDEX idx_suppliers_category ON parties.suppliers(supplier_category);
CREATE INDEX idx_territories_org ON parties.territories(org_id);
CREATE INDEX idx_routes_territory ON parties.routes(territory_id);

-- Full text search indexes
CREATE INDEX idx_customers_search ON parties.customers 
    USING gin(to_tsvector('english', customer_name || ' ' || COALESCE(customer_code, '')));
CREATE INDEX idx_suppliers_search ON parties.suppliers 
    USING gin(to_tsvector('english', supplier_name || ' ' || COALESCE(supplier_code, '')));

-- Add comments
COMMENT ON TABLE parties.customers IS 'Customer master with Indian pharma specific fields like drug license';
COMMENT ON TABLE parties.suppliers IS 'Supplier master with quality ratings and compliance tracking';
COMMENT ON TABLE parties.territories IS 'Geographic territory management for sales and distribution';
COMMENT ON TABLE parties.routes IS 'Delivery and sales route planning';