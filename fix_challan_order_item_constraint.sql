-- Fix the challan_items foreign key constraint issue
-- Challans should be able to exist without order_items

-- First, drop the foreign key constraint that requires order_item_id
ALTER TABLE challan_items 
DROP CONSTRAINT IF EXISTS challan_items_order_item_id_fkey;

-- Make order_item_id nullable since direct challans won't have order items
ALTER TABLE challan_items 
ALTER COLUMN order_item_id DROP NOT NULL;

-- This allows challans to be created directly without orders
-- The workflow now supports:
-- 1. Direct Challan (no order) → Invoice
-- 2. Order → Challan → Invoice