# 🚂 Railway Deployment Guide

## Prerequisites
- Railway account (https://railway.app)
- Railway CLI installed (optional)

## 🚀 Quick Deploy Steps

### Option 1: Deploy via GitHub (Recommended)

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   git remote add origin https://github.com/YOUR_USERNAME/pharma-backend.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to https://railway.app/new
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect and deploy

### Option 2: Deploy via CLI

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

## 🔧 Environment Variables

After deployment, add these in Railway dashboard:

```env
# Database (Your Supabase URL)
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# Security
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200

# App Settings
APP_ENV=production
APP_NAME="Pharma Management System"
APP_VERSION=2.0.0
DEBUG=False
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]

# Database Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=True

# Optional
SENTRY_DSN=your-sentry-dsn
```

## 📋 Post-Deployment Checklist

1. **Check deployment logs**
   ```bash
   railway logs
   ```

2. **Test endpoints**
   ```bash
   curl https://YOUR-APP.railway.app/health
   ```

3. **Update frontend API URL**
   - Update your frontend to use the Railway URL

## 🚨 Troubleshooting

### Common Issues:

1. **Module not found errors**
   - Ensure all imports use absolute paths
   - Check requirements.txt is complete

2. **Database connection fails**
   - Verify DATABASE_URL is correct
   - Check Supabase allows Railway's IP

3. **Port binding error**
   - Railway provides $PORT automatically
   - Don't hardcode port numbers

### Useful Commands:
```bash
# View logs
railway logs

# Open dashboard
railway open

# Restart deployment
railway restart

# Set environment variable
railway variables set KEY=value
```

## 🎯 Next Steps

1. **Monitor deployment**
   - Check Railway metrics dashboard
   - Set up health check monitoring

2. **Configure custom domain**
   - Add custom domain in Railway settings
   - Update DNS records

3. **Set up CI/CD**
   - Enable auto-deploy on push
   - Configure preview environments

## 📊 Expected Performance

- **Cold start**: ~5-10 seconds
- **Response time**: <200ms average
- **Memory usage**: ~256MB
- **CPU usage**: <10% idle

## 🔒 Security Notes

- All environment variables are encrypted
- Enable force HTTPS in Railway settings
- Review CORS settings for production
- Rotate JWT secret key regularly

---

Your backend will be live at: `https://YOUR-APP-NAME.railway.app`

API docs available at: `https://YOUR-APP-NAME.railway.app/docs`