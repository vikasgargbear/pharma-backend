# AASO Pharma Deployment Guide

## Current Infrastructure

### Production Environment
```
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY.APP (Backend)                     │
├─────────────────────────────────────────────────────────────┤
│ Service: pharma-backend                                      │
│ URL: https://pharma-backend-production-0c09.up.railway.app  │
│ Region: US West                                              │
│ Deploy: Automatic from GitHub main branch                    │
│ Build: Nixpacks (auto-detected Python)                      │
│ Start: uvicorn api.main:app --host 0.0.0.0 --port $PORT    │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                    SUPABASE (Database)                       │
├─────────────────────────────────────────────────────────────┤
│ Project: xfytbzavuvpbmxkhqvkb                              │
│ Database: PostgreSQL 15                                      │
│ Region: AWS us-east-1                                       │
│ Connection: Pooled + SSL Required                           │
│ URL: db.xfytbzavuvpbmxkhqvkb.supabase.co                  │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables

### Required in Railway
```bash
# Database
DATABASE_URL=postgresql://postgres:xxx@db.xfytbzavuvpbmxkhqvkb.supabase.co:5432/postgres?sslmode=require

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT  # Railway provides this
DEBUG=false
API_PREFIX=/api/v1

# Security
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Business Settings
TIMEZONE=Asia/Kolkata
CURRENCY=INR
COMPANY_NAME=Aaso Pharmaceuticals Pvt Ltd

# Monitoring
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## Deployment Process

### 1. Initial Setup (One-time)

#### Railway Setup
1. Create account at railway.app
2. Create new project
3. Connect GitHub repository
4. Configure environment variables
5. Deploy from main branch

#### Supabase Setup
1. Create account at supabase.com
2. Create new project
3. Note connection string
4. Enable row-level security
5. Configure connection pooling

### 2. Regular Deployment Flow

```mermaid
graph LR
    A[Local Development] --> B[Git Push to main]
    B --> C[Railway Auto-Deploy]
    C --> D[Build & Test]
    D --> E[Deploy to Production]
    E --> F[Health Check]
    F --> G[Live]
```

### 3. Database Migrations

#### Manual Migration Process
```bash
# 1. Connect to production database
psql $DATABASE_URL

# 2. Run migration scripts
\i migrations/001_initial_schema.sql
\i migrations/002_add_billing_tables.sql

# 3. Verify migration
\dt
```

#### Through API Endpoint
```bash
# Check migration status
curl https://pharma-backend-production-0c09.up.railway.app/migrations/status

# Run specific migration
curl -X POST https://pharma-backend-production-0c09.up.railway.app/migrations/billing/run
```

### 4. Deployment Checklist

#### Pre-deployment
- [ ] All tests passing locally
- [ ] Database migrations tested
- [ ] Environment variables updated
- [ ] API documentation updated
- [ ] Breaking changes documented

#### Deployment
- [ ] Push to main branch
- [ ] Monitor Railway build logs
- [ ] Check deployment status
- [ ] Verify health endpoint
- [ ] Run smoke tests

#### Post-deployment
- [ ] Test critical endpoints
- [ ] Check error logs
- [ ] Monitor performance
- [ ] Update status page
- [ ] Notify team

## Monitoring & Debugging

### Health Checks
```bash
# Basic health
curl https://pharma-backend-production-0c09.up.railway.app/health

# Detailed health
curl https://pharma-backend-production-0c09.up.railway.app/health/detailed

# Readiness check
curl https://pharma-backend-production-0c09.up.railway.app/health/readiness
```

### Logs
```bash
# Railway CLI
railway logs -n 100

# Through Railway dashboard
# Project > Service > Logs tab
```

### Common Issues & Solutions

#### 1. Database Connection Failed
```
Error: connection to server at "xxx.supabase.co" failed
```
**Solution**: 
- Check DATABASE_URL format
- Ensure ?sslmode=require is included
- Verify Supabase project is active

#### 2. Port Binding Error
```
Error: bind: address already in use
```
**Solution**:
- Use $PORT environment variable
- Don't hardcode port numbers

#### 3. Module Import Errors
```
ModuleNotFoundError: No module named 'api'
```
**Solution**:
- Ensure proper Python path
- Check requirements.txt
- Verify build commands

#### 4. Migration Failed
```
Error: relation "xxx" already exists
```
**Solution**:
- Check migration history
- Use IF NOT EXISTS clauses
- Implement proper rollback

## Rollback Procedures

### Code Rollback
1. Identify last working commit
2. Revert in GitHub
3. Railway auto-deploys
4. Verify functionality

### Database Rollback
1. Have backup ready
2. Create rollback script
3. Test in staging first
4. Execute with transaction
5. Verify data integrity

## Performance Optimization

### Railway Settings
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Database Optimization
1. **Connection Pooling**: Use Supabase pooler endpoint
2. **Indexes**: Add on frequently queried columns
3. **Query Optimization**: Use EXPLAIN ANALYZE
4. **Caching**: Implement Redis for hot data

### API Optimization
1. **Pagination**: Limit default page size
2. **Async Operations**: Use background tasks
3. **Response Compression**: Enable gzip
4. **CDN**: Use Cloudflare for static assets

## Security Best Practices

### Environment Variables
- Never commit .env files
- Use Railway's secret management
- Rotate keys regularly
- Use different keys per environment

### Database Security
- Enable RLS in Supabase
- Use least privilege principle
- Regular security audits
- Encrypt sensitive data

### API Security
- Implement rate limiting
- Use HTTPS only
- Validate all inputs
- Implement CORS properly

## Backup & Recovery

### Database Backups
1. **Automatic**: Supabase daily backups
2. **Manual**: pg_dump for critical operations
3. **Testing**: Regular restore tests

### Code Backups
1. **Git**: Multiple remotes
2. **Branches**: Protected main branch
3. **Tags**: Version releases

## Scaling Strategy

### Vertical Scaling
- Upgrade Railway plan
- Increase Supabase resources
- Optimize code performance

### Horizontal Scaling
- Multiple Railway services
- Database read replicas
- Load balancer setup
- Cache layer (Redis)

## Disaster Recovery

### RTO (Recovery Time Objective): 1 hour
### RPO (Recovery Point Objective): 1 hour

### Recovery Steps
1. **Identify Issue**: Check monitoring
2. **Assess Impact**: Determine scope
3. **Execute Recovery**: Follow runbook
4. **Verify Systems**: Run health checks
5. **Post-Mortem**: Document learnings

## Support Contacts

### Railway
- Dashboard: railway.app/dashboard
- Status: status.railway.app
- Support: support@railway.app

### Supabase
- Dashboard: app.supabase.com
- Status: status.supabase.com
- Support: support@supabase.com

### Internal
- On-call: [Define rotation]
- Escalation: [Define process]
- Documentation: This guide

## Cost Management

### Current Costs (Estimated)
- Railway Starter: $5/month
- Supabase Free Tier: $0/month
- Total: ~$5/month

### Scaling Costs
- Railway Team: $20/month
- Supabase Pro: $25/month
- Monitoring: $10/month
- Total: ~$55/month

## Future Improvements

1. **CI/CD Pipeline**: GitHub Actions
2. **Staging Environment**: Separate deployment
3. **Automated Testing**: Pre-deploy checks
4. **Monitoring**: Datadog/New Relic
5. **CDN**: Cloudflare integration
6. **Backup**: Automated off-site backups
7. **Security**: Web Application Firewall