-- =============================================
-- DISABLE: Automatic Batch Creation Trigger
-- =============================================
-- This disables the automatic batch creation trigger
-- because we're handling batch creation in the API
-- =============================================

-- Disable the trigger that automatically creates batches
DROP TRIGGER IF EXISTS trigger_create_batches_from_purchase ON purchases;

-- Keep the function for reference but comment about it being disabled
COMMENT ON FUNCTION create_batches_from_purchase() IS 
'DISABLED: Batch creation is now handled by the API during goods receipt to avoid conflicts';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '
=============================================
AUTOMATIC BATCH CREATION DISABLED
=============================================
✓ Trigger removed from purchases table
✓ Batch creation now handled by API only
✓ This prevents duplicate batch errors
=============================================';
END $$;