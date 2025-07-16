# 📤 GitHub Push Instructions

## ✅ Git Repository Ready!

Your code is committed and ready to push. Follow these steps:

## 1. Create GitHub Repository

Go to GitHub and create a new repository:
1. Visit: https://github.com/new
2. Repository name: `pharma-backend` (or your preferred name)
3. Description: "Pharmaceutical Management System Backend - FastAPI + PostgreSQL"
4. Keep it **Private** if it contains sensitive data
5. **DON'T** initialize with README (we already have one)
6. Click "Create repository"

## 2. Add Remote and Push

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/vikasgargbear/pharma-backend.git

# Push to GitHub
git push -u origin main
```

If you named your repo differently, replace `pharma-backend` with your repo name.

## 3. Verify Push

After pushing, refresh your GitHub repository page. You should see all your files.

## 4. Deploy to Railway

Now you can deploy to Railway:

### Option A: From Railway Dashboard
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your newly created repository
4. Railway will automatically detect and deploy

### Option B: Using Railway CLI
```bash
railway login
railway init
railway link  # Link to your Railway project
railway up
```

## 5. Add Environment Variables in Railway

After deployment starts, add these in Railway dashboard:

```env
DATABASE_URL=postgresql+psycopg2://postgres:I5ejcC77brqe4EPY@db.gjvgieqwkruvtsbthtez.supabase.co:5432/postgres
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
APP_ENV=production
DEBUG=False
ALLOWED_ORIGINS=["https://your-frontend-domain.com","http://localhost:3000"]
```

## 🎯 Quick Commands Summary

```bash
# If you haven't created the GitHub repo yet:
# 1. Go create it on GitHub first
# 2. Then run:
git remote add origin https://github.com/vikasgargbear/YOUR-REPO-NAME.git
git push -u origin main

# To check your remote:
git remote -v

# If you need to change the remote URL:
git remote set-url origin https://github.com/vikasgargbear/NEW-REPO-NAME.git
```

## 🚀 What Happens Next?

1. Your code will be on GitHub
2. Deploy via Railway (takes ~5 minutes)
3. Your API will be live at: `https://YOUR-APP.railway.app`
4. Test with: `curl https://YOUR-APP.railway.app/health`

## 📝 Notes

- Your git username: `vikasgargbear`
- Make sure you're logged into GitHub in your browser
- If asked for credentials, use your GitHub username and a Personal Access Token (not password)

Ready to push! 🎉