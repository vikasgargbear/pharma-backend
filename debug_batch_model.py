#!/usr/bin/env python3
"""
Debug script to check what columns SQLAlchemy thinks the Batch model has
"""

import sys
import os
sys.path.append('/Users/vikasgarg/Documents/AASO/Infrastructure/pharma-backend')

try:
    from api.models import Batch
    print("✅ Successfully imported Batch model")
    
    print("\n📋 Batch model columns:")
    for col in Batch.__table__.columns:
        print(f"  {col.name}: {col.type} (Python attr: {col.key})")
        
    print("\n🔍 Checking for mfg_date attribute:")
    if hasattr(Batch, 'mfg_date'):
        print("  ❌ Found mfg_date attribute!")
    else:
        print("  ✅ No mfg_date attribute found")
        
    print("\n🔍 Checking for manufacturing_date attribute:")
    if hasattr(Batch, 'manufacturing_date'):
        print("  ✅ Found manufacturing_date attribute!")
    else:
        print("  ❌ No manufacturing_date attribute found")
        
    print("\n🔍 All attributes:")
    for attr in dir(Batch):
        if not attr.startswith('_') and not callable(getattr(Batch, attr)):
            print(f"  {attr}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()