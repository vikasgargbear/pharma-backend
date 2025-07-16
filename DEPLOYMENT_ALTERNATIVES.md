# 🚀 Alternative Deployment Options

Since Railway has account limitations, here are other excellent free options:

## 1. **Render.com** (Recommended) ⭐
**Free tier: 750 hours/month**

### Deploy Steps:
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select `pharma-backend` repository
6. Configure:
   - Name: `pharma-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
7. Add environment variables
8. Click "Create Web Service"

### Create render.yaml:
```yaml
services:
  - type: web
    name: pharma-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        value: postgresql+psycopg2://postgres:I5ejcC77brqe4EPY@db.gjvgieqwkruvtsbthtez.supabase.co:5432/postgres
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: APP_ENV
        value: production
```

## 2. **Fly.io** (Fast & Global)
**Free tier: 3 shared VMs**

### Deploy Steps:
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly launch
fly deploy

# Set secrets
fly secrets set DATABASE_URL="your-db-url"
fly secrets set JWT_SECRET_KEY="your-secret"
```

## 3. **Koyeb** (Simple & Fast)
**Free tier: 1 app, 512MB RAM**

1. Visit https://koyeb.com
2. Sign up with GitHub
3. Create new app from GitHub
4. Select your repository
5. Auto-detects Python
6. Add environment variables
7. Deploy!

## 4. **Vercel** (For Serverless)
**Free tier: Generous limits**

Create `vercel.json`:
```json
{
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/main.py"
    }
  ]
}
```

Deploy:
```bash
npm i -g vercel
vercel
```

## 5. **Google Cloud Run** (Pay per use)
**Free tier: 2 million requests/month**

```bash
# Install gcloud CLI
# Build container
gcloud builds submit --tag gcr.io/PROJECT-ID/pharma-backend

# Deploy
gcloud run deploy --image gcr.io/PROJECT-ID/pharma-backend --platform managed
```

## 6. **Heroku** (If you have credits)
**No longer free, but reliable**

```bash
heroku create pharma-backend
git push heroku main
heroku config:set DATABASE_URL="your-db-url"
```

## 🎯 **Recommended: Use Render.com**

Render is the most similar to Railway and has a generous free tier:
- Easy GitHub integration
- Automatic deployments
- Free PostgreSQL database
- Custom domains
- SSL certificates

## 📋 Quick Render Deployment:

1. Sign up at https://render.com
2. New → Web Service
3. Connect GitHub
4. Select your repo
5. It auto-detects everything!

Your app will be live at: `https://pharma-backend.onrender.com`

---

**Note**: All these services support your existing configuration (Procfile, requirements.txt, etc.) with minimal or no changes!