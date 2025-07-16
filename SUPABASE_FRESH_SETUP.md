# 🚀 Fresh Supabase Setup Guide - South Asia Region

## 📍 Step 1: Create New Supabase Project

### Regional Considerations:
1. **Choose South Asia Region** when creating project:
   - Select `ap-south-1` (Mumbai) for lowest latency
   - Or `ap-southeast-1` (Singapore) as alternative

2. **Project Settings:**
   - Project Name: `aaso-pharma-erp`
   - Organization: Your company
   - Pricing Plan: Start with Free, upgrade to Pro when needed

## 📋 Step 2: Configure Project Settings

### Essential Settings:
1. **Authentication > Settings:**
   - ✅ Enable Email Auth
   - ✅ Disable Email Confirmations (for easier testing)
   - ✅ Enable Row Level Security
   - ❌ Disable Phone Auth (unless needed)

2. **Database > Settings:**
   - ✅ Enable Extensions: `uuid-ossp`, `pg_cron`
   - ✅ Set Timezone: `Asia/Kolkata` or your local timezone

3. **API > Settings:**
   - Note down your Project URL: `https://[project-id].supabase.co`
   - Note down your Anon Key: `eyJ...`
   - Note down your Service Role Key: `eyJ...` (keep secret!)

## 🗄️ Step 3: Setup Database Schema

Run these files **in exact order** in Supabase SQL Editor:

```bash
# Core ERP Schema (Required)
1. database/supabase/00_supabase_prep.sql
2. database/supabase/01_core_schema.sql  
3. database/supabase/01a_supabase_modifications.sql
4. database/supabase/01c_enterprise_critical_schema.sql
5. database/supabase/02_business_functions.sql
6. database/supabase/02b_additional_functions.sql
7. database/supabase/03_triggers_automation.sql
8. database/supabase/03b_additional_triggers.sql
9. database/supabase/04_indexes_performance.sql
10. database/supabase/04b_additional_indexes.sql
11. database/supabase/05_security_rls_supabase.sql
12. database/supabase/06_initial_data_production.sql

# Financial Module (Optional but Recommended)
13. database/supabase/FINANCIAL_MODULE/01_financial_core_schema.sql
14. database/supabase/FINANCIAL_MODULE/02_financial_functions.sql
15. database/supabase/FINANCIAL_MODULE/03_financial_triggers.sql
16. database/supabase/FINANCIAL_MODULE/04_financial_indexes.sql
17. database/supabase/FINANCIAL_MODULE/05_financial_security.sql
18. database/supabase/FINANCIAL_MODULE/06_financial_initial_data.sql

# AI Features (Optional)
19. supabase-migration/migrations/001_create_ai_tables.sql

# Simple Auth (Recommended for testing)
20. database/supabase/SIMPLE_BYPASS.sql
```

## 🔐 Step 4: Setup Authentication

### Create Your Admin User:
1. **Go to Supabase Dashboard > Authentication > Users**
2. **Click "Add User"**
3. **Enter:**
   - Email: `vikasgarg304@gmail.com`
   - Password: `Admin123!` (or your choice)
   - ✅ Auto Confirm User

### Test Login:
1. **Update** `database/supabase/working-login.html`:
   ```javascript
   const SUPABASE_URL = 'https://[your-project-id].supabase.co';
   const SUPABASE_ANON_KEY = 'your-anon-key-here';
   ```
2. **Open in browser and test login**

## 🔧 Step 5: Configure Your Backend

### Update Environment Variables:
Create `.env` file in `pharma-backend/`:
```bash
# Supabase
SUPABASE_URL=https://[your-project-id].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Database
DATABASE_URL=postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres?sslmode=require

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Regional Settings
TIMEZONE=Asia/Kolkata
CURRENCY=INR
COUNTRY=IN
```

### Update Database Connection:
In `api/database.py`:
```python
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

## 🌏 Step 6: South Asia Specific Configurations

### Indian Pharmaceutical Compliance:
1. **Tax Settings** (in initial data):
   - GST rates: 5%, 12%, 18%, 28%
   - HSN codes for pharmaceutical products
   - State codes for Indian states

2. **Currency & Localization**:
   - Default currency: INR (₹)
   - Date format: DD/MM/YYYY
   - Number format: 1,00,000 (Indian numbering)

3. **Drug Schedule Compliance**:
   - Schedule H, H1, X classifications
   - Prescription requirements
   - Storage temperature requirements

### Timezone & Working Hours:
```sql
-- Set default timezone for the database
ALTER DATABASE postgres SET timezone TO 'Asia/Kolkata';

-- Update business hours in organizations table
UPDATE organizations 
SET business_hours = jsonb_build_object(
  'monday', '09:00-18:00',
  'tuesday', '09:00-18:00', 
  'wednesday', '09:00-18:00',
  'thursday', '09:00-18:00',
  'friday', '09:00-18:00',
  'saturday', '09:00-14:00',
  'sunday', 'closed'
),
timezone = 'Asia/Kolkata';
```

## 🧪 Step 7: Test Everything

### Basic Tests:
1. **Authentication**: Login with your admin user
2. **Database**: Check if all tables exist
3. **API**: Test a simple endpoint
4. **RLS**: Verify user can only see their org data

### Test Commands:
```bash
# Start your backend
cd pharma-backend
python start_server.py

# Test API endpoints
python test_production_api.py
```

## 🚀 Step 8: Deploy AI Features (Optional)

### Deploy Edge Functions:
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref [your-project-id]

# Deploy edge functions
supabase functions deploy ai-chat --project-ref [your-project-id]
supabase functions deploy voice-process --project-ref [your-project-id]
```

## 🔒 Step 9: Security Checklist

### Production Security:
- [ ] Enable RLS on all tables
- [ ] Create proper API policies  
- [ ] Set up CORS origins
- [ ] Enable SSL certificates
- [ ] Configure rate limiting
- [ ] Set up monitoring & alerts

### Regional Compliance:
- [ ] GDPR compliance (if serving EU customers)
- [ ] Indian IT Act compliance
- [ ] Data residency requirements
- [ ] Pharmaceutical regulatory compliance

## 📈 Step 10: Performance Optimization

### For South Asia Region:
1. **CDN Configuration**: Use CloudFlare with Asia-Pacific edge locations
2. **Caching Strategy**: Redis cache for frequent queries
3. **Database Indexing**: All indexes are included in our schema files
4. **Connection Pooling**: Configure PgBouncer for high concurrency

## 🎯 Success Checklist

When setup is complete, you should have:
- ✅ Supabase project in South Asia region
- ✅ Complete pharmaceutical ERP database
- ✅ Working authentication system
- ✅ Indian compliance features
- ✅ Optional AI capabilities
- ✅ Financial management module
- ✅ Regional timezone & currency settings

## 🆘 Troubleshooting

### Common Issues:
1. **Auth errors**: Use SIMPLE_BYPASS.sql for testing
2. **RLS blocking**: Temporarily disable RLS during setup
3. **Connection issues**: Check DATABASE_URL format
4. **Regional latency**: Verify you selected ap-south-1 region

Your pharmaceutical ERP is now ready for South Asian market! 🇮🇳