# Supabase Database Setup

## Quick Start for New Supabase Project

1. **Create new Supabase project**
2. **Run these files in order in SQL Editor:**
   ```
   00_supabase_prep.sql
   01_core_schema.sql
   01a_supabase_modifications.sql
   01c_enterprise_critical_schema.sql
   02_business_functions.sql
   02b_additional_functions.sql
   03_triggers_automation.sql
   03b_additional_triggers.sql
   04_indexes_performance.sql
   04b_additional_indexes.sql
   05_security_rls_supabase.sql
   06_initial_data_production.sql
   ```

3. **For Financial Module (optional):**
   ```
   FINANCIAL_MODULE/01_financial_core_schema.sql
   FINANCIAL_MODULE/02_financial_functions.sql
   FINANCIAL_MODULE/03_financial_triggers.sql
   FINANCIAL_MODULE/04_financial_indexes.sql
   FINANCIAL_MODULE/05_financial_security.sql
   FINANCIAL_MODULE/06_financial_initial_data.sql
   ```

4. **For Simple Auth (bypasses Supabase auth issues):**
   ```
   SIMPLE_BYPASS.sql
   ```
   Then use `working-login.html` for testing

## What You Get

- Complete pharmaceutical ERP database
- Multi-tenant organization support
- Product, customer, order management
- Inventory tracking with batch management
- Financial accounting module
- Simple authentication system

## File Structure

- `00_*` - Core schema setup
- `01_*` - Business tables and modifications
- `02_*` - Business functions and procedures
- `03_*` - Triggers and automation
- `04_*` - Performance indexes
- `05_*` - Security and RLS policies
- `06_*` - Initial seed data
- `FINANCIAL_MODULE/` - Complete accounting system
- `SIMPLE_BYPASS.sql` - Working auth system
- `working-login.html` - Test login page

## Clean Start Instructions

1. Create fresh Supabase project
2. Update `working-login.html` with your Supabase URL and anon key
3. Run SQL files in order
4. Test with `working-login.html`
5. Integrate with your pharma-backend API

This gives you a production-ready pharmaceutical ERP database.