#!/bin/bash
# Cleanup script for old fix files
# These have been consolidated into V004__purchase_system_enhancements.sql

echo "This script will archive old SQL fix files that have been consolidated."
echo "The consolidated migration is in: database/migrations/V004__purchase_system_enhancements.sql"
echo ""
echo "Files to be archived:"
echo "- DISABLE_auto_batch_trigger.sql"
echo "- FIX_supplier_outstanding_trigger.sql"
echo "- FIX_batch_creation_trigger.sql"
echo "- FIX_batch_creation_trigger_v2.sql"
echo "- IMMEDIATE_FIX_purchase_trigger.sql"
echo "- UPDATE_inventory_movement_triggers.sql"
echo "- QUICK_FIX_purchase_trigger.sql"
echo ""
echo "To archive these files, create an 'archive' directory and move them:"
echo "mkdir -p database/supabase/archive"
echo "mv database/supabase/*FIX*.sql database/supabase/archive/"
echo "mv database/supabase/UPDATE*.sql database/supabase/archive/"
echo "mv database/supabase/DISABLE*.sql database/supabase/archive/"