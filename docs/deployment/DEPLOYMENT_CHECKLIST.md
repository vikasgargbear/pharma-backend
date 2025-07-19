# 🚀 Deployment Checklist

## Phase 1: Supabase Setup

### 1. Create Supabase Project
- [ ] Sign up at [supabase.com](https://supabase.com)
- [ ] Create new project
- [ ] Note down:
  - Project URL: `https://[PROJECT].supabase.co`
  - Anon Key: `eyJ...`
  - Service Role Key: `eyJ...` (keep secret!)
  - Database Password

### 2. Configure Database
- [ ] Go to SQL Editor in Supabase dashboard
- [ ] Run your database schema (from `database/production_ready_schema.sql`)
- [ ] Verify all tables are created
- [ ] Enable Row Level Security (RLS) for sensitive tables

### 3. Configure Storage
- [ ] Create a bucket named `pharma-files` for PDF storage
- [ ] Set bucket to private (requires authentication)
- [ ] Configure CORS if needed

## Phase 2: Backend Deployment (Railway/Render)

### 1. Prepare Backend for Deployment
- [ ] Update `requirements.txt` with all dependencies
- [ ] Create `.env.example` file with all required variables
- [ ] Update `api/config.py` to use environment variables:
  ```python
  DATABASE_URL = os.getenv("DATABASE_URL")
  SUPABASE_URL = os.getenv("SUPABASE_URL")
  SUPABASE_KEY = os.getenv("SUPABASE_KEY")
  ```

### 2. Deploy to Railway (Recommended)
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Login: `railway login`
- [ ] Initialize: `railway init`
- [ ] Set environment variables:
  ```bash
  railway variables set DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
  railway variables set SUPABASE_URL="https://[PROJECT].supabase.co"
  railway variables set SUPABASE_KEY="your-anon-key"
  railway variables set SECRET_KEY="generate-secure-key"
  railway variables set JWT_SECRET_KEY="another-secure-key"
  railway variables set ENVIRONMENT="production"
  ```
- [ ] Deploy: `railway up`
- [ ] Note your backend URL: `https://your-app.railway.app`

### 3. Alternative: Deploy to Render
- [ ] Create account at [render.com](https://render.com)
- [ ] Connect GitHub repository
- [ ] Create new Web Service
- [ ] Configure:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables in Render dashboard

## Phase 3: Test Backend APIs

### 1. Update Test Script
- [ ] Edit `test_production_api.py`
- [ ] Update `BASE_URL` with your deployed backend URL
- [ ] Run: `python test_production_api.py`

### 2. Verify Core Functionality
- [ ] Health check endpoint works
- [ ] Database connection successful
- [ ] User registration/login works
- [ ] CRUD operations for all entities
- [ ] File upload to Supabase storage works

## Phase 4: Frontend Deployment (Vercel)

### 1. Prepare Frontend
- [ ] Update API base URL in frontend config:
  ```javascript
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-backend.railway.app'
  ```
- [ ] Build locally to test: `npm run build`
- [ ] Fix any build errors

### 2. Deploy to Vercel
- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] Login: `vercel login`
- [ ] Deploy: `vercel` (in frontend directory)
- [ ] Configure environment variables in Vercel dashboard:
  - `REACT_APP_API_URL`: Your backend URL
  - `REACT_APP_SUPABASE_URL`: Your Supabase URL
  - `REACT_APP_SUPABASE_ANON_KEY`: Your Supabase anon key

### 3. Configure Custom Domain (Optional)
- [ ] Add custom domain in Vercel dashboard
- [ ] Update DNS records
- [ ] Enable HTTPS (automatic)

## Phase 5: Production Configuration

### 1. Security
- [ ] Enable CORS in backend for your frontend domain
- [ ] Set up rate limiting
- [ ] Configure secure headers
- [ ] Enable HTTPS everywhere
- [ ] Rotate all development secrets

### 2. Monitoring
- [ ] Set up Sentry for error tracking (free tier)
- [ ] Configure Uptimerobot for uptime monitoring (free)
- [ ] Enable Railway/Render logs
- [ ] Set up alerts for critical errors

### 3. Backup Strategy
- [ ] Enable Supabase automatic backups
- [ ] Set up manual backup script (optional)
- [ ] Document recovery procedures

## Phase 6: Performance Optimization

### 1. Database
- [ ] Add indexes for frequently queried columns
- [ ] Enable connection pooling in Supabase
- [ ] Optimize slow queries

### 2. API
- [ ] Implement caching headers
- [ ] Add pagination to all list endpoints
- [ ] Optimize file upload size limits

### 3. Frontend
- [ ] Enable lazy loading
- [ ] Optimize bundle size
- [ ] Configure CDN for static assets

## Additional Services to Consider

### Essential (Free/Low Cost)
1. **Email Service**: SendGrid or Resend (for order confirmations)
2. **SMS Service**: Twilio (for critical alerts) - pay as you go
3. **Analytics**: Google Analytics or Plausible
4. **Error Tracking**: Sentry (5K errors/month free)

### Nice to Have
5. **CDN**: Cloudflare (free tier)
6. **Queue Service**: Railway Redis ($10/month) for background jobs
7. **Search**: Algolia (free tier) for product search
8. **Monitoring**: New Relic (free tier)

## Post-Deployment Checklist

- [ ] Test complete user journey (order placement to delivery)
- [ ] Verify email notifications work
- [ ] Check mobile responsiveness
- [ ] Test under load (use loader.io free tier)
- [ ] Document all environment variables
- [ ] Create runbook for common issues
- [ ] Set up staging environment (optional)

## Troubleshooting Common Issues

### Database Connection Errors
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check Supabase status
curl https://[PROJECT].supabase.co/rest/v1/
```

### CORS Issues
Add to backend:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variable Issues
- Double-check all variables are set
- Restart services after updating
- Use Railway/Render logs to debug

## Success Metrics

- [ ] All API endpoints return < 500ms response time
- [ ] 99.9% uptime achieved
- [ ] Zero critical security vulnerabilities
- [ ] Successful order processing end-to-end
- [ ] Positive user feedback

---

Remember: Start with the minimum viable deployment, then iterate based on actual usage!