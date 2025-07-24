-- =====================================================================================
-- ADD STATE CODE COLUMN TO CUSTOMERS TABLE
-- =====================================================================================
-- Purpose: Add state_code column for proper GST calculations (CGST/SGST vs IGST)
-- Author: System
-- Date: 2025-07-24
-- =====================================================================================

-- Add state_code column
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS state_code VARCHAR(2);

-- Add comment for documentation
COMMENT ON COLUMN customers.state_code IS 'Two-digit GST state code for tax calculations';

-- =====================================================================================
-- UPDATE EXISTING RECORDS WITH STATE CODES
-- =====================================================================================

-- Karnataka (most common in current data)
UPDATE customers 
SET state_code = '29' 
WHERE LOWER(TRIM(state)) = 'karnataka' 
AND state_code IS NULL;

-- Other states in alphabetical order
UPDATE customers SET state_code = '28' WHERE LOWER(TRIM(state)) = 'andhra pradesh' AND state_code IS NULL;
UPDATE customers SET state_code = '12' WHERE LOWER(TRIM(state)) = 'arunachal pradesh' AND state_code IS NULL;
UPDATE customers SET state_code = '18' WHERE LOWER(TRIM(state)) = 'assam' AND state_code IS NULL;
UPDATE customers SET state_code = '10' WHERE LOWER(TRIM(state)) = 'bihar' AND state_code IS NULL;
UPDATE customers SET state_code = '22' WHERE LOWER(TRIM(state)) = 'chhattisgarh' AND state_code IS NULL;
UPDATE customers SET state_code = '30' WHERE LOWER(TRIM(state)) = 'goa' AND state_code IS NULL;
UPDATE customers SET state_code = '24' WHERE LOWER(TRIM(state)) = 'gujarat' AND state_code IS NULL;
UPDATE customers SET state_code = '06' WHERE LOWER(TRIM(state)) = 'haryana' AND state_code IS NULL;
UPDATE customers SET state_code = '02' WHERE LOWER(TRIM(state)) = 'himachal pradesh' AND state_code IS NULL;
UPDATE customers SET state_code = '20' WHERE LOWER(TRIM(state)) = 'jharkhand' AND state_code IS NULL;
UPDATE customers SET state_code = '32' WHERE LOWER(TRIM(state)) = 'kerala' AND state_code IS NULL;
UPDATE customers SET state_code = '23' WHERE LOWER(TRIM(state)) = 'madhya pradesh' AND state_code IS NULL;
UPDATE customers SET state_code = '27' WHERE LOWER(TRIM(state)) = 'maharashtra' AND state_code IS NULL;
UPDATE customers SET state_code = '14' WHERE LOWER(TRIM(state)) = 'manipur' AND state_code IS NULL;
UPDATE customers SET state_code = '17' WHERE LOWER(TRIM(state)) = 'meghalaya' AND state_code IS NULL;
UPDATE customers SET state_code = '15' WHERE LOWER(TRIM(state)) = 'mizoram' AND state_code IS NULL;
UPDATE customers SET state_code = '13' WHERE LOWER(TRIM(state)) = 'nagaland' AND state_code IS NULL;
UPDATE customers SET state_code = '21' WHERE LOWER(TRIM(state)) = 'odisha' AND state_code IS NULL;
UPDATE customers SET state_code = '03' WHERE LOWER(TRIM(state)) = 'punjab' AND state_code IS NULL;
UPDATE customers SET state_code = '08' WHERE LOWER(TRIM(state)) = 'rajasthan' AND state_code IS NULL;
UPDATE customers SET state_code = '11' WHERE LOWER(TRIM(state)) = 'sikkim' AND state_code IS NULL;
UPDATE customers SET state_code = '33' WHERE LOWER(TRIM(state)) = 'tamil nadu' AND state_code IS NULL;
UPDATE customers SET state_code = '36' WHERE LOWER(TRIM(state)) = 'telangana' AND state_code IS NULL;
UPDATE customers SET state_code = '16' WHERE LOWER(TRIM(state)) = 'tripura' AND state_code IS NULL;
UPDATE customers SET state_code = '09' WHERE LOWER(TRIM(state)) = 'uttar pradesh' AND state_code IS NULL;
UPDATE customers SET state_code = '05' WHERE LOWER(TRIM(state)) = 'uttarakhand' AND state_code IS NULL;
UPDATE customers SET state_code = '19' WHERE LOWER(TRIM(state)) = 'west bengal' AND state_code IS NULL;
UPDATE customers SET state_code = '07' WHERE LOWER(TRIM(state)) = 'delhi' AND state_code IS NULL;
UPDATE customers SET state_code = '01' WHERE LOWER(TRIM(state)) = 'jammu and kashmir' AND state_code IS NULL;
UPDATE customers SET state_code = '38' WHERE LOWER(TRIM(state)) = 'ladakh' AND state_code IS NULL;

-- Union Territories
UPDATE customers SET state_code = '04' WHERE LOWER(TRIM(state)) = 'chandigarh' AND state_code IS NULL;
UPDATE customers SET state_code = '34' WHERE LOWER(TRIM(state)) = 'puducherry' AND state_code IS NULL;
UPDATE customers SET state_code = '35' WHERE LOWER(TRIM(state)) = 'andaman and nicobar islands' AND state_code IS NULL;
UPDATE customers SET state_code = '26' WHERE LOWER(TRIM(state)) = 'dadra and nagar haveli and daman and diu' AND state_code IS NULL;
UPDATE customers SET state_code = '31' WHERE LOWER(TRIM(state)) = 'lakshadweep' AND state_code IS NULL;

-- =====================================================================================
-- CREATE INDEX FOR PERFORMANCE
-- =====================================================================================
CREATE INDEX IF NOT EXISTS idx_customers_state_code ON customers(state_code);

-- =====================================================================================
-- VERIFICATION
-- =====================================================================================
DO $$
DECLARE
    total_count INTEGER;
    with_code_count INTEGER;
    without_code_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM customers;
    SELECT COUNT(*) INTO with_code_count FROM customers WHERE state_code IS NOT NULL;
    without_code_count := total_count - with_code_count;
    
    RAISE NOTICE 'State code migration completed:';
    RAISE NOTICE '  Total customers: %', total_count;
    RAISE NOTICE '  With state code: %', with_code_count;
    RAISE NOTICE '  Without state code: %', without_code_count;
    
    IF without_code_count > 0 THEN
        RAISE NOTICE '  ⚠️  Some customers still need state codes. Check states that are not in the mapping.';
    ELSE
        RAISE NOTICE '  ✅ All customers have state codes!';
    END IF;
END $$;

-- =====================================================================================
-- SAMPLE QUERY TO CHECK UNMAPPED STATES
-- =====================================================================================
-- Run this to see which states don't have mappings:
-- SELECT DISTINCT state, COUNT(*) as customer_count 
-- FROM customers 
-- WHERE state_code IS NULL 
-- GROUP BY state 
-- ORDER BY customer_count DESC;