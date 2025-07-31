#!/bin/bash

# Supabase Free Plan Backup Script
# This works with the free plan using direct connection

echo "==================================="
echo "Supabase Free Plan Backup Script"
echo "==================================="

# You'll need to get these from your Supabase dashboard
echo "Please enter your Supabase database details:"
echo "(Find these in Supabase Dashboard > Settings > Database)"
echo

read -p "Database Host (e.g., db.xxxxx.supabase.co): " DB_HOST
read -p "Database Password: " -s DB_PASSWORD
echo

# Fixed values for Supabase
DB_USER="postgres"
DB_NAME="postgres"
DB_PORT="5432"

# Create backup directory
BACKUP_DIR="./database_backups"
mkdir -p $BACKUP_DIR

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting backup..."

# Export password to avoid prompt
export PGPASSWORD=$DB_PASSWORD

# Create full backup
pg_dump -h $DB_HOST \
  -U $DB_USER \
  -d $DB_NAME \
  -p $DB_PORT \
  --no-owner \
  --no-privileges \
  --no-tablespaces \
  --no-unlogged-table-data \
  --no-comments \
  --exclude-schema=auth \
  --exclude-schema=storage \
  --exclude-schema=graphql* \
  --exclude-schema=realtime \
  --exclude-schema=_analytics \
  --exclude-schema=_realtime \
  --exclude-schema=supabase_functions \
  --exclude-schema=extensions \
  --exclude-schema=net \
  --exclude-schema=vault \
  --schema=public \
  > "$BACKUP_DIR/pharma_backup_$TIMESTAMP.sql"

# Unset password
unset PGPASSWORD

# Check if backup was successful
if [ -s "$BACKUP_DIR/pharma_backup_$TIMESTAMP.sql" ]; then
    FILE_SIZE=$(ls -lh "$BACKUP_DIR/pharma_backup_$TIMESTAMP.sql" | awk '{print $5}')
    echo "✅ Backup successful!"
    echo "📁 File: $BACKUP_DIR/pharma_backup_$TIMESTAMP.sql"
    echo "📊 Size: $FILE_SIZE"
    
    # Compress the backup
    echo "Compressing backup..."
    gzip "$BACKUP_DIR/pharma_backup_$TIMESTAMP.sql"
    echo "✅ Compressed to: $BACKUP_DIR/pharma_backup_$TIMESTAMP.sql.gz"
else
    echo "❌ Backup failed! Check your credentials and try again."
    exit 1
fi