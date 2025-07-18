-- =============================================
-- 13. Database Cleanup - Remove Redundant Columns
-- =============================================
-- This migration removes redundant columns identified in the data dictionary
-- Run this AFTER backing up your data!
-- Created: 2025-07-18

-- =============================================
-- 13.1 Backup important data before cleanup
-- =============================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== IMPORTANT: Backup your database before running this migration! ===';
    RAISE NOTICE 'This script will remove redundant columns from the customers table.';
    RAISE NOTICE '';
    
    -- Show current redundant data
    RAISE NOTICE 'Checking redundant columns in customers table...';
END $$;

-- Show sample of redundant data
SELECT 
    COUNT(*) as total_customers,
    COUNT(landmark) as has_landmark,
    COUNT(area) as has_area,
    COUNT(CASE WHEN landmark IS NOT NULL AND area IS NULL THEN 1 END) as landmark_only,
    COUNT(CASE WHEN landmark = area THEN 1 END) as same_values
FROM customers;

-- =============================================
-- 13.2 Migrate data from redundant columns
-- =============================================

-- Ensure area field has all landmark data
UPDATE customers 
SET area = landmark 
WHERE area IS NULL AND landmark IS NOT NULL;

-- Ensure gstin has all gst_number data
UPDATE customers 
SET gstin = gst_number 
WHERE gstin IS NULL AND gst_number IS NOT NULL;

-- Ensure credit_days has all credit_period_days data
UPDATE customers 
SET credit_days = credit_period_days 
WHERE credit_days IS NULL AND credit_period_days IS NOT NULL;

-- Ensure address_line1 has all address data
UPDATE customers 
SET address_line1 = address 
WHERE address_line1 IS NULL AND address IS NOT NULL;

-- =============================================
-- 13.3 Create backup table (optional safety)
-- =============================================
CREATE TABLE IF NOT EXISTS customers_backup_20250718 AS 
SELECT * FROM customers;

-- =============================================
-- 13.4 Drop redundant columns
-- =============================================
DO $$
BEGIN
    -- Drop landmark (replaced by area)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'customers' AND column_name = 'landmark') THEN
        ALTER TABLE customers DROP COLUMN landmark;
        RAISE NOTICE 'Dropped column: landmark (replaced by area)';
    END IF;
    
    -- Drop business_type (redundant with customer_type)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'customers' AND column_name = 'business_type') THEN
        ALTER TABLE customers DROP COLUMN business_type;
        RAISE NOTICE 'Dropped column: business_type (redundant with customer_type)';
    END IF;
    
    -- Drop gst_number (replaced by gstin)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'customers' AND column_name = 'gst_number') THEN
        ALTER TABLE customers DROP COLUMN gst_number;
        RAISE NOTICE 'Dropped column: gst_number (replaced by gstin)';
    END IF;
    
    -- Drop credit_period_days (replaced by credit_days)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'customers' AND column_name = 'credit_period_days') THEN
        ALTER TABLE customers DROP COLUMN credit_period_days;
        RAISE NOTICE 'Dropped column: credit_period_days (replaced by credit_days)';
    END IF;
    
    -- Drop address (replaced by address_line1)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'customers' AND column_name = 'address') THEN
        ALTER TABLE customers DROP COLUMN address;
        RAISE NOTICE 'Dropped column: address (replaced by address_line1)';
    END IF;
    
    -- Note: Not dropping contact_person as it serves a different purpose
    -- Note: Not dropping notes as it contains user-entered data
END $$;

-- =============================================
-- 13.5 Add missing useful columns
-- =============================================
DO $$
BEGIN
    -- Add contact_person if missing (for B2B customers)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'contact_person') THEN
        ALTER TABLE customers ADD COLUMN contact_person VARCHAR(100);
        RAISE NOTICE 'Added column: contact_person';
    END IF;
    
    -- Add address_line2 if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'customers' AND column_name = 'address_line2') THEN
        ALTER TABLE customers ADD COLUMN address_line2 VARCHAR(200);
        RAISE NOTICE 'Added column: address_line2';
    END IF;
END $$;

-- =============================================
-- 13.6 Optimize data types
-- =============================================
-- Convert status fields to more efficient types
DO $$
BEGIN
    -- This is commented out for safety - uncomment if you want to optimize
    -- ALTER TABLE customers ALTER COLUMN customer_type TYPE VARCHAR(20);
    -- ALTER TABLE customers ALTER COLUMN preferred_payment_mode TYPE VARCHAR(20);
    -- ALTER TABLE orders ALTER COLUMN order_status TYPE VARCHAR(20);
    -- ALTER TABLE orders ALTER COLUMN payment_status TYPE VARCHAR(20);
    
    RAISE NOTICE 'Data type optimization skipped (uncomment if needed)';
END $$;

-- =============================================
-- 13.7 Create optimized indexes
-- =============================================
-- Drop redundant indexes if any
DROP INDEX IF EXISTS idx_customers_landmark;
DROP INDEX IF EXISTS idx_customers_business_type;

-- Ensure important indexes exist
CREATE INDEX IF NOT EXISTS idx_customers_area ON customers(area) WHERE area IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_customer_type ON customers(customer_type);
CREATE INDEX IF NOT EXISTS idx_customers_city_state ON customers(city, state);
CREATE INDEX IF NOT EXISTS idx_customers_outstanding ON customers(outstanding_amount) WHERE outstanding_amount > 0;

-- =============================================
-- 13.8 Update views that might reference dropped columns
-- =============================================
-- If you have any views using the dropped columns, recreate them here

-- =============================================
-- 13.9 Final verification
-- =============================================
DO $$
DECLARE
    col_count integer;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns 
    WHERE table_name = 'customers';
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Cleanup Complete ===';
    RAISE NOTICE 'Customers table now has % columns', col_count;
    RAISE NOTICE 'Backup table created: customers_backup_20250718';
    RAISE NOTICE 'Removed redundant columns: landmark, business_type, gst_number, credit_period_days, address';
    RAISE NOTICE '';
    RAISE NOTICE 'To restore if needed:';
    RAISE NOTICE 'ALTER TABLE customers ADD COLUMN landmark TEXT;';
    RAISE NOTICE 'UPDATE customers c SET landmark = b.landmark FROM customers_backup_20250718 b WHERE c.customer_id = b.customer_id;';
    RAISE NOTICE '=======================';
END $$;

-- Show final structure
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'customers'
ORDER BY ordinal_position;