# 🔐 Fix GitHub Authentication Error

## The Problem
GitHub no longer accepts passwords. You need a Personal Access Token (PAT).

## 🚀 Quick Fix - Two Options:

### Option 1: Use SSH (Easiest)

1. **Change remote to SSH:**
```bash
git remote set-url origin git@github.com:vikasgargbear/pharma-backend.git
```

2. **Check if you have SSH key:**
```bash
ls ~/.ssh/id_*
```

3. **If no SSH key exists, create one:**
```bash
ssh-keygen -t ed25519 -C "160091032+vikasgargbear@users.noreply.github.com"
# Press Enter for all prompts
```

4. **Add SSH key to GitHub:**
```bash
# Copy your public key
cat ~/.ssh/id_ed25519.pub
```
- Go to https://github.com/settings/keys
- Click "New SSH key"
- Paste the key and save

5. **Push again:**
```bash
git push -u origin main
```

### Option 2: Create Personal Access Token

1. **Go to GitHub Settings:**
   - https://github.com/settings/tokens
   - Click "Generate new token (classic)"

2. **Configure token:**
   - Note: "Pharma Backend Deployment"
   - Expiration: 90 days (or your preference)
   - Select scopes:
     - ✅ repo (all)
     - ✅ workflow

3. **Copy the token** (you'll see it only once!)

4. **Use token as password:**
```bash
git push -u origin main
# Username: vikasgargbear
# Password: [PASTE YOUR TOKEN HERE]
```

### Option 3: Use GitHub CLI (Alternative)

1. **Install GitHub CLI:**
```bash
brew install gh
```

2. **Authenticate:**
```bash
gh auth login
# Choose: GitHub.com
# Choose: HTTPS
# Choose: Login with web browser
```

3. **Push using gh:**
```bash
gh repo create pharma-backend --private --source=. --remote=origin --push
```

## 🎯 Recommended: Use SSH (Option 1)

SSH is more secure and you won't need to enter credentials again.

## 📝 Quick SSH Setup Commands:
```bash
# Switch to SSH
git remote set-url origin git@github.com:vikasgargbear/pharma-backend.git

# Generate SSH key if needed
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy SSH key
cat ~/.ssh/id_ed25519.pub

# Test SSH connection
ssh -T git@github.com

# Push
git push -u origin main
```

## 🚨 If Token Method:
- Save your token securely
- Tokens expire - set a reminder
- Never commit tokens to code

Choose SSH for easier long-term use! 🔐