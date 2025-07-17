#!/usr/bin/env python3
"""
Pre-deployment test to catch import errors
Run this before pushing to avoid deployment failures

Usage: python test_imports.py
"""

import sys
import traceback

def test_imports():
    """Test all critical imports to catch errors before deployment"""
    errors = []
    
    print("🔍 Testing imports...")
    
    # Test models import
    try:
        from api import models
        print("✅ Models imported successfully")
        
        # Check for models referenced in routers
        required_models = [
            'Product', 'Batch', 'Customer', 'Order', 'OrderItem',
            'Payment', 'Supplier', 'Purchase', 'User', 'Organization',
            'InventoryMovement', 'SalesReturn', 'Challan', 'ChallanItem',
            'TaxEntry', 'Category', 'UnitOfMeasure', 'OrgUser', 'OrgBranch',
            'PriceList'
        ]
        
        missing_models = []
        for model_name in required_models:
            if not hasattr(models, model_name):
                missing_models.append(model_name)
        
        if missing_models:
            errors.append(f"Missing models: {', '.join(missing_models)}")
            print(f"❌ Missing models: {', '.join(missing_models)}")
        else:
            print("✅ All required models found")
            
    except Exception as e:
        errors.append(f"Failed to import models: {str(e)}")
        print(f"❌ Failed to import models: {str(e)}")
        traceback.print_exc()
    
    # Test schemas import
    try:
        from api import schemas
        print("✅ Schemas imported successfully")
    except Exception as e:
        errors.append(f"Failed to import schemas: {str(e)}")
        print(f"❌ Failed to import schemas: {str(e)}")
        traceback.print_exc()
    
    # Test crud import
    try:
        from api import crud
        print("✅ CRUD imported successfully")
    except Exception as e:
        errors.append(f"Failed to import crud: {str(e)}")
        print(f"❌ Failed to import crud: {str(e)}")
        traceback.print_exc()
    
    # Test each router - only test the ones we're actually importing
    enabled_routers = [
        'analytics', 'batches', 'orders', 'products', 
        'simple_delivery', 'tax_entries', 'db_inspect'
    ]
    
    disabled_routers = [
        'compliance', 'customers', 'file_uploads', 'inventory', 
        'loyalty', 'payments', 'purchases', 'sales_returns', 
        'stock_adjustments', 'users'
    ]
    
    routers = enabled_routers  # Only test enabled routers
    
    print("\n🔍 Testing router imports...")
    for router_name in routers:
        try:
            module = __import__(f'api.routers.{router_name}', fromlist=[router_name])
            print(f"✅ Router '{router_name}' imported successfully")
        except Exception as e:
            errors.append(f"Failed to import router '{router_name}': {str(e)}")
            print(f"❌ Failed to import router '{router_name}': {str(e)}")
            if "AuditLog" in str(e):
                print("   → Compliance router needs AuditLog model")
    
    # Test main app import
    try:
        from api import main
        print("\n✅ Main app imported successfully")
    except Exception as e:
        errors.append(f"Failed to import main app: {str(e)}")
        print(f"\n❌ Failed to import main app: {str(e)}")
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print(f"❌ FAILED: {len(errors)} errors found:")
        for error in errors:
            print(f"  • {error}")
        print("\n⚠️  DO NOT DEPLOY - Fix these errors first!")
        return False
    else:
        print("✅ ALL TESTS PASSED - Safe to deploy!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)