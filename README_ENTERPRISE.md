# Enterprise Pharmaceutical ERP Backend

A world-class, enterprise-grade pharmaceutical ERP backend built on PostgreSQL/Supabase, designed specifically for the Indian pharmaceutical industry.

## 🚀 Features

- **Multi-tenant Architecture**: Complete organization isolation with row-level security
- **Pharmaceutical Pack Hierarchy**: Tablet → Strip → Box → Case management
- **GST Compliance**: GSTR-1, GSTR-2A, GSTR-3B, E-way bill generation
- **Narcotic Drug Tracking**: Schedule X compliance with balance verification
- **Double-entry Bookkeeping**: Complete financial integrity
- **Real-time Inventory**: Multi-location stock with FEFO/FIFO allocation
- **Comprehensive APIs**: 40+ REST-style PostgreSQL functions
- **Analytics Dashboard**: Executive KPIs and business intelligence

## 📋 Prerequisites

- Supabase account (or PostgreSQL 13+)
- Node.js 16+ (for frontend integration)
- Basic knowledge of PostgreSQL and REST APIs

## 🛠️ Installation

### Step 1: Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create a new project
3. Save your project credentials:
   - Project URL: `https://YOUR_PROJECT_REF.supabase.co`
   - Anon Key: `your-anon-key`
   - Service Role Key: `your-service-role-key` (keep secure!)

### Step 2: Deploy Database Schema

1. Open your Supabase project's SQL Editor
2. Run the deployment scripts in this order:

```sql
-- Enable required extensions first
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Then run each file in sequence:
-- 1. Create API schema
-- 2. Create all 10 schemas (master, inventory, etc.)
-- 3. Create views for backward compatibility
-- 4. Create all triggers
-- 5. Create business functions
-- 6. Create performance indexes
-- 7. Load initial data
-- 8. Create all APIs
```

Or use the complete deployment script:

```bash
# Clone the repository
git clone <your-repo-url>
cd pharma-backend/database/enterprise-v2

# Update Supabase connection in deployment script
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" \
  -f 09-deployment/01_deploy_to_supabase.sql
```

### Step 3: Configure Environment Variables

Create a `.env` file in your frontend/backend application:

```env
# Supabase Configuration
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Application Settings
APP_NAME="Pharma ERP"
DEFAULT_ORG_ID=1
CURRENCY=INR
GST_ENABLED=true
```

### Step 4: Update Security Settings

1. Go to Supabase Dashboard → Authentication → Policies
2. Enable RLS on all tables (already done in deployment)
3. Configure email templates for authentication

### Step 5: Initialize Master Data

Run the initialization script to set up your organization:

```sql
-- Update organization details
UPDATE master.organizations 
SET 
  company_name = 'Your Pharma Company Ltd',
  legal_name = 'Your Pharma Company Private Limited',
  gstin = 'YOUR_GSTIN',
  pan_number = 'YOUR_PAN',
  drug_license_number = 'YOUR_LICENSE',
  registered_address = jsonb_build_object(
    'address_line1', 'Your Address',
    'city', 'Your City',
    'state', 'Your State',
    'pincode', 'Your Pincode'
  )
WHERE org_id = 1;

-- Create admin user (update email/password)
UPDATE system_config.users
SET 
  email = 'admin@yourcompany.com',
  password_hash = encode(digest('YourSecurePassword', 'sha256'), 'hex')
WHERE user_id = 1;
```

## 🔌 API Integration

### JavaScript/TypeScript Example

```javascript
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
)

// Authentication
async function login(username, password) {
  const { data, error } = await supabase.rpc('authenticate_user', {
    p_username: username,
    p_password: password
  })
  
  if (error) throw error
  
  // Store session token
  localStorage.setItem('session_token', data.session.token)
  return data
}

// Search Products
async function searchProducts(searchTerm) {
  const { data, error } = await supabase.rpc('search_products', {
    p_search_term: searchTerm,
    p_limit: 20
  })
  
  return data.products
}

// Create Invoice
async function createInvoice(invoiceData) {
  const { data, error } = await supabase.rpc('create_invoice', {
    p_invoice_data: {
      org_id: 1,
      branch_id: 1,
      customer_id: invoiceData.customerId,
      items: invoiceData.items.map(item => ({
        product_id: item.productId,
        quantity: item.quantity,
        base_unit_price: item.price,
        discount_percentage: item.discount || 0,
        tax_percentage: item.gst || 12
      }))
    }
  })
  
  if (error) throw error
  return data
}

// Get Dashboard
async function getDashboard() {
  const { data, error } = await supabase.rpc('get_executive_dashboard', {
    p_org_id: 1,
    p_date_range: 'current_month'
  })
  
  return data
}
```

### React Integration Example

```jsx
// hooks/useProducts.js
import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase'

export function useProducts(searchTerm) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    async function fetchProducts() {
      setLoading(true)
      
      const { data, error } = await supabase.rpc('search_products', {
        p_search_term: searchTerm,
        p_limit: 50
      })
      
      if (!error) {
        setProducts(data.products)
      }
      
      setLoading(false)
    }
    
    if (searchTerm) {
      fetchProducts()
    }
  }, [searchTerm])
  
  return { products, loading }
}
```

## 📊 Database Structure

### Schemas
- **master**: Organizations, branches, product categories, UOMs
- **inventory**: Products, batches, stock, movements
- **parties**: Customers, suppliers, categories
- **sales**: Orders, invoices, returns, schemes
- **procurement**: Purchase orders, GRN, supplier returns
- **financial**: Journal entries, payments, outstanding
- **gst**: GSTR data, e-way bills, returns
- **compliance**: Licenses, narcotic register, inspections
- **analytics**: KPIs, customer behavior, product performance
- **system_config**: Users, roles, settings, audit

### Key Tables
- 135 tables optimized for pharmaceutical operations
- 75+ triggers for business logic automation
- 400+ indexes for performance optimization

## 🔒 Security

### Row Level Security (RLS)
All tables have RLS enabled with policies for organization isolation:

```sql
-- Example: Users can only see their organization's data
CREATE POLICY "org_isolation" ON inventory.products
  FOR ALL USING (org_id = auth.org_id());
```

### Authentication
- JWT-based authentication via Supabase Auth
- Session management with expiry
- Failed login attempt tracking
- Password policies enforcement

### Audit Trail
Complete audit logging for:
- All data modifications
- User actions
- System events
- Compliance tracking

## 🧪 Testing

Run the comprehensive test suite:

```sql
-- Run all tests
SELECT * FROM testing.run_all_tests();

-- Generate test report
SELECT testing.generate_test_report();
```

Test categories:
- Inventory management
- Financial integrity
- GST calculations
- Compliance rules
- Performance benchmarks

## 📈 Monitoring

### Health Checks
```sql
-- System health status
SELECT * FROM api.system_health_check();

-- Performance metrics
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

### Key Metrics
- Database size and growth
- Query performance
- Index usage
- Cache hit ratios

## 🔧 Maintenance

### Regular Tasks
1. **Daily**: Monitor error logs, check system health
2. **Weekly**: Run ANALYZE, review slow queries
3. **Monthly**: VACUUM ANALYZE, index maintenance
4. **Quarterly**: Security audit, performance review

### Backup Strategy
- Supabase automatic daily backups
- Point-in-time recovery available
- Export critical data regularly

## 📚 API Documentation

Complete API documentation available in `/database/enterprise-v2/08-api/API_DOCUMENTATION.md`

### Key API Endpoints

#### Master Data
- `get_organization_details()`
- `search_products()`
- `get_product_details()`

#### Sales
- `search_customers()`
- `create_sales_order()`
- `create_invoice()`
- `get_sales_dashboard()`

#### Inventory
- `get_stock_availability()`
- `get_batch_information()`
- `get_reorder_alerts()`

#### Financial
- `record_payment()`
- `get_customer_outstanding()`
- `get_profit_loss_statement()`

#### Analytics
- `get_executive_dashboard()`
- `get_sales_analytics()`
- `get_inventory_analytics()`

## 🚨 Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify Supabase URL and keys
   - Check network connectivity
   - Ensure RLS policies are correct

2. **Permission Errors**
   - Verify user roles and permissions
   - Check RLS policies
   - Ensure proper authentication

3. **Performance Issues**
   - Run ANALYZE on tables
   - Check index usage
   - Monitor connection pooling

### Debug Queries
```sql
-- Check recent errors
SELECT * FROM system_config.error_log 
WHERE created_at > NOW() - INTERVAL '1 hour';

-- View audit trail
SELECT * FROM system_config.audit_log 
WHERE table_name = 'invoices' 
ORDER BY created_at DESC LIMIT 20;
```

## 📞 Support

### Documentation
- Implementation Guide: `/database/enterprise-v2/ENTERPRISE_IMPLEMENTATION_GUIDE.md`
- API Reference: `/database/enterprise-v2/08-api/API_DOCUMENTATION.md`
- Schema Documentation: In each schema SQL file

### Getting Help
1. Check the comprehensive documentation
2. Run the test suite to identify issues
3. Review audit logs for errors
4. Check Supabase logs in dashboard

## 🎯 Roadmap

- [ ] Mobile app APIs
- [ ] Advanced analytics
- [ ] AI-powered insights
- [ ] Multi-currency support
- [ ] Advanced forecasting

## 📄 License

This project is proprietary software. All rights reserved.

---

Built with ❤️ for the pharmaceutical industry