#!/usr/bin/env python3
"""Test script to validate new product API schema"""

import json
from api.schemas_v2.product_schema import ProductCreate, ProductResponse, ProductUpdate
from api.base_schemas import ProductCreate as BaseProductCreate
from pydantic import ValidationError

def test_product_create_schema():
    """Test the new ProductCreate schema"""
    print("Testing ProductCreate schema...")
    
    # Test valid product data
    product_data = {
        "product_name": "Test Medicine",
        "product_code": "TEST001",
        "manufacturer": "Test Pharma",
        "hsn_code": "30049099",
        "category": "Tablet",
        "salt_composition": "Paracetamol 500mg",
        "mrp": 100.00,
        "sale_price": 90.00,
        "cost_price": 70.00,
        "gst_percent": 12,
        "base_unit": "Tablet",
        "sale_unit": "Strip",
        "quantity_received": 100,
        "expiry_date": "2025-12-01",
        
        # New pack fields
        "pack_input": "10*10",
        "pack_quantity": 10,
        "pack_multiplier": 10,
        "pack_unit_type": None,
        "unit_count": 10,
        "unit_measurement": None,
        "packages_per_box": 10
    }
    
    try:
        # Test with new schema
        product = ProductCreate(**product_data)
        print("✓ ProductCreate validation successful")
        print(f"  Generated product_code: {product.product_code}")
        print(f"  Pack input: {product.pack_input}")
        
        # Test with base schema
        base_product = BaseProductCreate(**product_data)
        print("✓ BaseProductCreate validation successful")
        
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
        return False
    
    return True

def test_product_response_schema():
    """Test the ProductResponse schema"""
    print("\nTesting ProductResponse schema...")
    
    from datetime import datetime
    
    response_data = {
        "product_id": 1,
        "org_id": "12de5e22-eee7-4d25-b3a7-d16d01c6170f",
        "product_name": "Test Medicine",
        "product_code": "TEST001",
        "manufacturer": "Test Pharma",
        "hsn_code": "30049099",
        "category": "Tablet",
        "salt_composition": "Paracetamol 500mg",
        "mrp": 100.00,
        "sale_price": 90.00,
        "cost_price": 70.00,
        "gst_percent": 12,
        "base_unit": "Tablet",
        "sale_unit": "Strip",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "pack_config": {
            "pack_input": "10*10",
            "pack_quantity": 10,
            "pack_multiplier": 10,
            "pack_unit_type": None,
            "unit_count": 10,
            "unit_measurement": None,
            "packages_per_box": 10
        }
    }
    
    try:
        response = ProductResponse(**response_data)
        print("✓ ProductResponse validation successful")
        print(f"  Pack config: {response.pack_config.model_dump()}")
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
        return False
    
    return True

def test_product_update_schema():
    """Test the ProductUpdate schema"""
    print("\nTesting ProductUpdate schema...")
    
    update_data = {
        "sale_price": 95.00,
        "pack_input": "10*20",
        "pack_multiplier": 20,
        "packages_per_box": 20
    }
    
    try:
        update = ProductUpdate(**update_data)
        print("✓ ProductUpdate validation successful")
        print(f"  Update fields: {update.model_dump(exclude_unset=True)}")
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
        return False
    
    return True

def test_pack_input_validation():
    """Test pack input format validation"""
    print("\nTesting pack input formats...")
    
    test_cases = [
        ("10*10", 10, 10, None),
        ("1*100ML", 1, 100, "ML"),
        ("1*200", 1, 200, None),
        ("30", 30, None, None)
    ]
    
    for pack_input, expected_qty, expected_mult, expected_unit in test_cases:
        product_data = {
            "product_name": "Test",
            "manufacturer": "Test",
            "hsn_code": "12345",
            "category": "Tablet",
            "mrp": 100,
            "sale_price": 90,
            "cost_price": 70,
            "gst_percent": 12,
            "base_unit": "Unit",
            "sale_unit": "Unit",
            "pack_input": pack_input,
            "pack_quantity": expected_qty,
            "pack_multiplier": expected_mult,
            "pack_unit_type": expected_unit
        }
        
        try:
            product = ProductCreate(**product_data)
            print(f"✓ Pack input '{pack_input}' validated successfully")
        except ValidationError as e:
            print(f"✗ Pack input '{pack_input}' failed: {e}")

if __name__ == "__main__":
    print("Running Product API Schema Tests...")
    print("=" * 50)
    
    all_passed = True
    all_passed &= test_product_create_schema()
    all_passed &= test_product_response_schema()
    all_passed &= test_product_update_schema()
    test_pack_input_validation()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All schema tests passed!")
    else:
        print("❌ Some tests failed")