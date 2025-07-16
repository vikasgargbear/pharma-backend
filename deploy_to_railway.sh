#!/bin/bash

# Railway CLI Deployment Script
echo "🚂 Railway Deployment Script"
echo "=========================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo ""
echo "📋 Follow these steps:"
echo ""
echo "1. Run this command to login:"
echo "   railway login"
echo ""
echo "2. After login, run:"
echo "   railway init"
echo "   (Create a new project when prompted)"
echo ""
echo "3. Deploy your code:"
echo "   railway up"
echo ""
echo "4. Add environment variables:"
echo "   railway variables set DATABASE_URL=\"postgresql+psycopg2://postgres:I5ejcC77brqe4EPY@db.gjvgieqwkruvtsbthtez.supabase.co:5432/postgres\""
echo "   railway variables set JWT_SECRET_KEY=\"your-super-secret-key-change-this\""
echo "   railway variables set APP_ENV=\"production\""
echo "   railway variables set DEBUG=\"False\""
echo ""
echo "5. Get your app URL:"
echo "   railway domain"
echo ""
echo "=========================="
echo "Ready to deploy! Start with: railway login"