# 🚂 Update Railway to Use Your Supabase Database

## Step 1: Get Your Supabase Connection String

1. Go to your Supabase project dashboard
2. Navigate to Settings → Database
3. Find the "Connection string" section
4. Copy the "URI" (it should look like):
   ```
   postgresql://postgres.[your-project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

## Step 2: Format for Railway

Convert the Supabase URI to SQLAlchemy format by adding `+psycopg2`:

**From:**
```
postgresql://postgres.kfhlcqracxvxkqllwywd:lkiSF948fj2jf8ejfkKJ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

**To:**
```
postgresql+psycopg2://postgres.kfhlcqracxvxkqllwywd:lkiSF948fj2jf8ejfkKJ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

## Step 3: Update Railway Environment Variables

### Option A: Via Railway Dashboard (Recommended)
1. Go to https://railway.app/dashboard
2. Select your `pharma-backend` project
3. Click on the service
4. Go to "Variables" tab
5. Find `DATABASE_URL` 
6. Update it with your Supabase connection string (with `+psycopg2`)
7. Railway will automatically redeploy

### Option B: Via Railway CLI
```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Update the DATABASE_URL
railway variables set DATABASE_URL="postgresql+psycopg2://postgres.kfhlcqracxvxkqllwywd:lkiSF948fj2jf8ejfkKJ@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

# Deploy the changes
railway up
```

## Step 4: Verify the Update

After Railway redeploys (takes 2-3 minutes):

1. Check the deployment logs in Railway dashboard
2. You should see:
   ```
   ✅ Using existing PostgreSQL tables: postgresql+psycopg2://postgres.kfhlcqrac...
   📊 Connection pool size: 10
   🔄 Database type: PostgreSQL (Supabase)
   ```

3. Test by creating a new invoice - it should now appear in your Supabase dashboard!

## Important Notes

⚠️ **WARNING**: This will make Railway use YOUR Supabase database. Any existing data in Railway's database will not be accessible unless you switch back.

✅ **BENEFITS**: 
- All data will be in your Supabase instance
- You can view/manage data through Supabase dashboard
- Consistent data across all environments

## Rollback (if needed)

To revert to Railway's database, simply remove the `DATABASE_URL` variable from Railway, and it will use its default PostgreSQL instance.

## Troubleshooting

If you see connection errors:
1. Check if your Supabase project allows connections from Railway's IP
2. Ensure the password is correct (no special characters that need escaping)
3. Try using the "Session pooler" connection string instead of "Transaction pooler"