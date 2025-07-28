-- Add org_id to challans table for multi-tenant support
-- This is critical for businesses with multiple locations/organizations

ALTER TABLE challans 
ADD COLUMN IF NOT EXISTS org_id UUID DEFAULT '12de5e22-eee7-4d25-b3a7-d16d01c6170f';

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_challans_org_id ON challans(org_id);

-- Update existing records to have the default org_id
UPDATE challans 
SET org_id = '12de5e22-eee7-4d25-b3a7-d16d01c6170f' 
WHERE org_id IS NULL;

-- Make it NOT NULL after updating existing records
ALTER TABLE challans 
ALTER COLUMN org_id SET NOT NULL;