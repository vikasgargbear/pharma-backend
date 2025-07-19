# 🚂 Railway Basic Plan Deployment Guide

## 💳 Railway Basic Plan Benefits
- **$5/month** of included usage
- **No sleeping apps** (always on)
- **Better performance**
- **Custom domains**
- **More resources**

## 🚀 After Upgrading to Basic Plan

### 1. **Deploy from GitHub Dashboard**
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `vikasgargbear/pharma-backend`
4. Railway will automatically:
   - Detect Python app
   - Use your Procfile
   - Install requirements
   - Start deployment

### 2. **Configure Environment Variables**
After deployment starts, go to your project settings and add:

```env
# Database (Supabase)
DATABASE_URL=postgresql+psycopg2://postgres:I5ejcC77brqe4EPY@db.gjvgieqwkruvtsbthtez.supabase.co:5432/postgres

# Security
JWT_SECRET_KEY=change-this-to-a-very-secure-random-string
JWT_ALGORITHM=HS256

# App Settings
APP_ENV=production
APP_NAME=Pharma Management System
APP_VERSION=2.0.0
DEBUG=False
LOG_LEVEL=INFO

# CORS (update with your frontend URL)
ALLOWED_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]

# Optional Performance Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=True
```

### 3. **Monitor Deployment**
- Watch the deployment logs
- First deployment may take 5-10 minutes
- Check for any errors

### 4. **Get Your App URL**
Railway will provide you with:
- Default URL: `https://your-app-name.railway.app`
- You can add custom domain later

## 📋 Post-Deployment Checklist

1. **Test Core Endpoints:**
   ```bash
   # Health check
   curl https://your-app.railway.app/health
   
   # API docs
   open https://your-app.railway.app/docs
   
   # System info
   curl https://your-app.railway.app/info
   ```

2. **Update Frontend:**
   - Change API URL to your Railway URL
   - Update CORS settings if needed

3. **Monitor Performance:**
   - Check Railway metrics dashboard
   - Monitor response times
   - Watch for errors

## 🔧 Troubleshooting

### If deployment fails:

1. **Check Build Logs:**
   - Look for missing dependencies
   - Check for import errors
   - Verify Python version compatibility

2. **Common Fixes:**
   - Ensure all dependencies are in requirements.txt
   - Check that DATABASE_URL is correct
   - Verify Procfile syntax

3. **Database Connection Issues:**
   - Whitelist Railway IPs in Supabase (if needed)
   - Check connection string format
   - Verify credentials

## 🎯 Expected Timeline

1. **Upgrade Plan**: 2 minutes
2. **Deploy from GitHub**: 5-10 minutes
3. **Configure Environment**: 5 minutes
4. **Testing**: 5 minutes

**Total: ~20 minutes to production!**

## 🚀 Quick Commands After Deployment

```bash
# View logs
railway logs

# Open dashboard
railway open

# Add more environment variables
railway variables set KEY=value

# Redeploy
railway up

# Get deployment URL
railway domain
```

## 📊 Performance Expectations

With Basic Plan:
- **Response Time**: <200ms average
- **Uptime**: 99.9%
- **Cold Starts**: None (always on)
- **Concurrent Requests**: Handles 100+ easily

## 🎉 Success Metrics

Your deployment is successful when:
1. Health endpoint returns 200
2. Database connection confirmed
3. API docs accessible
4. No errors in logs

---

**Ready to deploy! Your app will be production-ready in 20 minutes!** 🚀