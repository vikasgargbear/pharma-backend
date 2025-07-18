# AASO Pharma - Quick Reference Guide

## 🚨 Current System State (As of July 18, 2025)

### What's Working ✅
1. **Organizations API** - CRUD operations
2. **Customers API** - Full customer management with credit tracking
3. **Products API** - Product catalog with batch management
4. **Orders API** - Order creation, confirmation, delivery
5. **Basic Inventory** - Stock tracking through batches
6. **Database Connection** - Supabase PostgreSQL

### What's Pending ❌
1. **Billing Module** - Created but migration not run on production
2. **Invoice Generation** - Code ready, tables missing in production
3. **Authentication** - No user login system yet
4. **Reports** - No reporting endpoints implemented

### Known Issues 🐛
1. **Schema Mismatches**:
   - Orders table has `final_amount` but code expects `total_amount`
   - Order items has `selling_price` not `unit_price`
   - Batches has `quantity_sold` not `quantity_allocated`

2. **API Inconsistencies**:
   - Some endpoints use `/api/v1/` prefix, others don't
   - Mixed schema versions (base_schemas.py vs schemas_v2/)

3. **File Organization**:
   - Scattered routers (some in v1/, some in root)
   - Mixed naming conventions
   - No clear separation of concerns

## 🔧 Common Tasks

### Start Local Development
```bash
# Terminal 1 - Start PostgreSQL (if using local)
brew services start postgresql@14

# Terminal 2 - Start FastAPI
cd pharma-backend
source venv/bin/activate  # or your virtual env
uvicorn api.main:app --reload --port 8080
```

### Test Key Endpoints
```bash
# Health check
curl http://localhost:8080/health

# List customers
curl http://localhost:8080/api/v1/customers

# Create order
curl -X POST http://localhost:8080/api/v1/orders \
  -H "Content-Type: application/json" \
  -d @test_order.json

# Confirm order
curl -X POST http://localhost:8080/api/v1/orders/6/confirm
```

### Database Queries
```sql
-- Check orders
SELECT order_id, order_status, final_amount 
FROM orders 
ORDER BY created_at DESC LIMIT 5;

-- Check stock
SELECT p.product_name, b.batch_number, b.quantity_available
FROM products p
JOIN batches b ON p.product_id = b.product_id
WHERE b.quantity_available > 0;

-- Check customers
SELECT customer_id, customer_name, credit_limit
FROM customers
WHERE is_active = true;
```

### Deploy to Production
```bash
# Just push to main branch
git add .
git commit -m "feat: your feature"
git push origin main

# Railway auto-deploys
# Check status at: https://railway.app/dashboard
```

## 📁 Key Files Location

### Configuration
- `.env` - Environment variables (local)
- `api/core/config.py` - Settings management

### Database
- `api/database.py` - Database connection
- `api/models.py` - SQLAlchemy models (old)
- `api/migrations/` - Migration scripts

### API Endpoints
- `api/routers/v1/customers.py` - Customer endpoints
- `api/routers/v1/orders.py` - Order endpoints
- `api/routers/v1/billing.py` - Billing endpoints
- `api/routers/products.py` - Product endpoints (needs v1)

### Services
- `api/services/customer_service.py` - Customer logic
- `api/services/order_service.py` - Order logic
- `api/services/billing_service.py` - Billing logic

### Schemas
- `api/base_schemas.py` - Old schemas (being phased out)
- `api/schemas_v2/` - New schemas (preferred)

## 🌐 URLs

### Production
- **API**: https://pharma-backend-production-0c09.up.railway.app
- **Health**: https://pharma-backend-production-0c09.up.railway.app/health
- **Docs**: https://pharma-backend-production-0c09.up.railway.app/docs

### Database
- **Supabase Dashboard**: https://app.supabase.com/project/xfytbzavuvpbmxkhqvkb
- **Connection**: See `.env` file

### Deployment
- **Railway Dashboard**: https://railway.app/dashboard
- **GitHub Repo**: [Your repo URL]

## 🛠️ Troubleshooting

### "Module not found" Error
```bash
# Run from pharma-backend directory
python -m api.main
# OR
cd pharma-backend && uvicorn api.main:app
```

### Database Connection Failed
1. Check `.env` file has correct DATABASE_URL
2. Ensure `?sslmode=require` is in URL
3. Verify Supabase project is active

### Order Creation Fails
- Check customer exists and is active
- Ensure products and batches exist
- Verify batch has sufficient quantity

### Invoice Generation Fails
- Migration not run yet on production
- Run: `/migrations/billing/run` endpoint

## 📋 TODO Priority List

### Immediate (Do First)
1. Run billing migration on production
2. Fix schema mismatches in order tables
3. Standardize all APIs to `/api/v1/` prefix

### High Priority
1. Implement authentication system
2. Add user management
3. Complete billing module testing
4. Create admin dashboard

### Medium Priority
1. Add comprehensive reports
2. Implement email notifications
3. Add SMS integration
4. Create mobile API

### Nice to Have
1. GraphQL API
2. Webhook system
3. Real-time updates
4. Advanced analytics

## 💡 Development Tips

### Adding New Feature
1. Check existing patterns in codebase
2. Follow the structure in `SYSTEM_ARCHITECTURE.md`
3. Write service layer first, then API
4. Always add to the `/api/v1/` namespace
5. Update this quick reference!

### Common Patterns
```python
# Service pattern
class YourService:
    @staticmethod
    def your_method(db: Session, data: YourSchema):
        # Business logic here
        pass

# Router pattern
router = APIRouter(prefix="/api/v1/your-resource", tags=["your-tag"])

@router.post("/", response_model=YourResponse)
async def create_resource(
    data: YourCreate,
    db: Session = Depends(get_db)
):
    return YourService.create(db, data)
```

### Testing
```bash
# No automated tests yet!
# Test manually with curl or Postman
# Document test cases in /tests/ directory
```

## 🔐 Security Notes

1. **No Authentication Yet** - API is open!
2. **Default Org ID** - Hardcoded in routers
3. **No Rate Limiting** - In production
4. **Secrets in .env** - Don't commit!

## 📞 Getting Help

1. Check `SYSTEM_ARCHITECTURE.md` for design
2. Check `DATABASE_SCHEMA.md` for structure  
3. Check `DEPLOYMENT_GUIDE.md` for deployment
4. Check error logs in Railway dashboard
5. Check Supabase logs for DB issues

---

**Remember**: We're building an enterprise system. When in doubt:
- Follow existing patterns
- Keep it simple
- Document everything
- Test before deploying
- Ask for help early!