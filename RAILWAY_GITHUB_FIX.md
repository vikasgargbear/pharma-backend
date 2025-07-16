# 🔧 Fix Railway GitHub Connection

## Common Issues & Solutions:

### 1. **Check GitHub Integration**
First, ensure Railway has access to your GitHub:
- Go to: https://github.com/settings/installations
- Look for "Railway" in the list
- If not there, you need to authorize Railway

### 2. **Authorize Railway App**
1. In Railway dashboard, click your profile (top right)
2. Go to "Account Settings"
3. Click "Connected Accounts"
4. Click "Connect GitHub"
5. Authorize Railway to access your repositories

### 3. **Grant Repository Access**
If Railway is already connected but can't see your repo:
1. Go to: https://github.com/settings/installations
2. Click "Configure" next to Railway
3. Under "Repository access":
   - Select "All repositories" OR
   - Select "Only select repositories" and add `pharma-backend`
4. Click "Save"

### 4. **Alternative: Deploy via Railway CLI**

If GitHub integration still doesn't work, use CLI:

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize new project
railway init

# Deploy directly from your local code
railway up
```

### 5. **Alternative: Import from Git URL**

In Railway dashboard:
1. Click "New Project"
2. Select "Deploy from GitHub Repo"
3. Instead of searching, paste the full URL:
   ```
   https://github.com/vikasgargbear/pharma-backend
   ```

### 6. **Make Repository Public (Temporary)**

If nothing works, temporarily make your repo public:
1. Go to: https://github.com/vikasgargbear/pharma-backend/settings
2. Scroll to "Danger Zone"
3. Click "Change visibility"
4. Make it public
5. Try Railway again
6. Make it private after deployment

## 🚀 Quick Fix Steps:

1. **First, try this URL in Railway:**
   ```
   https://github.com/vikasgargbear/pharma-backend.git
   ```

2. **If that fails, check GitHub integration:**
   - https://railway.app/account
   - Reconnect GitHub

3. **If still failing, use CLI:**
   ```bash
   railway login
   railway init
   railway up
   ```

## 📝 Most Common Fix:

Usually, it's because Railway doesn't have permission to see your repositories. Go to GitHub Settings > Integrations > Railway and ensure it has access to your repos.

---

**Pro tip**: The Railway CLI method (`railway up`) always works because it uploads directly from your computer!