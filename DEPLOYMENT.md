# Deployment Guide

## Production Environment

### Current Deployment
- **Platform**: Railway
- **URL**: https://pharma-backend-production-0c09.up.railway.app
- **Database**: PostgreSQL on Supabase
- **Status**: ✅ Deployed, ❌ Some endpoints failing

### Quick Deploy Commands
```bash
# Push to trigger auto-deploy
git add .
git commit -m "Deploy updates"
git push origin main

# Railway will automatically deploy from main branch
```

## Environment Configuration

### Required Environment Variables
```env
# Database
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_KEY=[service_key]

# Authentication  
JWT_SECRET_KEY=[generate-random-key]
JWT_ALGORITHM=HS256

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Railway Setup
1. Connect GitHub repository
2. Set environment variables in Railway dashboard
3. Configure auto-deploy from main branch
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

## Database Setup

### Supabase Configuration
1. Create new project on Supabase
2. Get connection string from Settings → Database
3. Enable Row Level Security (RLS) on all tables
4. Create organization with UUID: `12de5e22-eee7-4d25-b3a7-d16d01c6170f`

### Database Migration
```bash
# If using Alembic (future)
alembic upgrade head

# Current: Database already exists with schema
# No migration needed - tables already created
```

## Health Checks

### Verify Deployment
```bash
# API health check
curl https://pharma-backend-production-0c09.up.railway.app/api/health

# Root endpoint
curl https://pharma-backend-production-0c09.up.railway.app/

# Database tools (requires auth)
curl https://pharma-backend-production-0c09.up.railway.app/api/database-tools/inspect-tables
```

## Troubleshooting

### Common Issues

#### 500 Errors on Product Endpoints
- **Cause**: Schema mismatch between models and database
- **Fix**: Align SQLAlchemy models with actual database schema
- **Status**: ❌ Currently broken

#### Database Connection Issues
- **Check**: Verify DATABASE_URL in Railway environment
- **Test**: Use `/api/health` endpoint
- **Fix**: Update connection string if needed

#### Import Errors
- **Cause**: Missing dependencies or circular imports
- **Fix**: Check import paths in routers and models
- **Status**: ✅ Most import issues resolved

### Logs and Monitoring
```bash
# View Railway logs
# Go to Railway dashboard → Project → Deployments → View logs

# Check specific errors
# Look for Python traceback in deployment logs
```

## Local Development

### Setup for Local Testing
```bash
# Clone and setup
git clone [repo-url]
cd pharma-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with local database connection

# Run locally
uvicorn api.main:app --reload --port 8000
```

### Testing Against Production Database
```env
# Use production database locally for testing
DATABASE_URL=postgresql://postgres:[password]@[supabase-host]:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_KEY=[service_key]
```

## Deployment Checklist

### Before Deploying
- [ ] All critical tests passing locally
- [ ] Environment variables configured
- [ ] Database schema matches models
- [ ] No hardcoded secrets in code
- [ ] Error handling implemented

### After Deploying
- [ ] Health check returns 200
- [ ] Database connection working
- [ ] Key endpoints responding
- [ ] No 500 errors in logs
- [ ] Performance acceptable

## Production Issues (Current)

### Known Problems
1. **Product endpoints failing** - 500 errors due to schema mismatches
2. **CRUD operations broken** - SQLAlchemy model issues  
3. **Search functionality** - Not working properly
4. **Missing validations** - Some endpoints lack proper validation

### Immediate Actions Needed
1. Fix SQLAlchemy models to match database schema
2. Test all endpoints thoroughly
3. Add proper error handling
4. Implement comprehensive logging

## Rollback Plan

### If Deployment Fails
```bash
# Revert to previous working commit
git revert HEAD
git push origin main

# Railway will auto-deploy the reverted version
```

### Manual Intervention
- Use Railway dashboard to redeploy previous version
- Check logs to identify specific failure points
- Test critical endpoints before marking as stable

---

*Current Status: API deployed but needs fixes for full functionality*