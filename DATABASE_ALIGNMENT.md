# Database Schema Alignment Report

## Current Issues

### 1. Products Table

#### Database Schema (Actual)
- `org_id`: UUID, NOT NULL ⚠️
- `alternate_barcodes`: ARRAY
- `tags`: ARRAY  
- `search_keywords`: ARRAY
- `pack_details`: JSONB

#### Model Definition (api/models.py)
- `org_id`: String, nullable ❌ (should be UUID, NOT NULL)
- `alternate_barcodes`: Text ❌ (should be array)
- `tags`: Text ❌ (should be array)
- `search_keywords`: Text ❌ (should be array)
- `pack_details`: JSON ✅

#### Schema Definition (api/schemas.py)
- `org_id`: Optional[str] ❌ (should be required UUID)
- `alternate_barcodes`: Optional[str] ❌ (should be List[str])
- `tags`: Optional[str] ❌ (should be List[str])
- `search_keywords`: Optional[str] ❌ (should be List[str])
- `pack_details`: Optional[dict] ✅

## Solution Approach

Instead of modifying the database (which could break existing data), we should:

1. **Fix Models** - Align SQLAlchemy models with actual database
2. **Fix Schemas** - Update Pydantic schemas to match
3. **Handle org_id** - Since it's required in DB, we need to either:
   - Generate a UUID when creating records
   - Get an existing org_id from the organizations table
   - Create a default organization

## Quick Fix for Testing

For immediate testing, we can:
1. Create a default organization in the database
2. Use that org_id for all test operations
3. Later implement proper multi-tenancy

## Long-term Solution

1. Review ALL tables and their schemas
2. Create proper migration scripts
3. Implement organization management
4. Add proper validation and defaults