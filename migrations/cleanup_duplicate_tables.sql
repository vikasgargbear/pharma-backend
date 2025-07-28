-- Cleanup duplicate tables created before seeing the schema
-- Only run this if you're sure these tables have no data

-- Drop the duplicate tables we created (without 's' at the end)
DROP TABLE IF EXISTS sale_return_items CASCADE;
DROP TABLE IF EXISTS sale_returns CASCADE;

-- The purchase_returns tables we created might also be duplicates
-- Check if they have the same structure as existing ones
-- DROP TABLE IF EXISTS purchase_return_items CASCADE;
-- DROP TABLE IF EXISTS purchase_returns CASCADE;

-- Drop the stock writeoff tables if not needed
-- These might be new functionality so check before dropping
-- DROP TABLE IF EXISTS stock_writeoff_items CASCADE;
-- DROP TABLE IF EXISTS stock_writeoffs CASCADE;
-- DROP TABLE IF EXISTS gst_adjustments CASCADE;