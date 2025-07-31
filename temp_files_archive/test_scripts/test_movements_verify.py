#!/usr/bin/env python3
"""Verify inventory movements were created correctly"""

import requests
import json
from collections import defaultdict

BASE_URL = "http://localhost:8000"

def get_movements():
    """Get all inventory movements grouped by type"""
    # This would normally query the database directly
    # For now, we'll check via the APIs
    
    movements = defaultdict(list)
    
    # Get sales returns
    response = requests.get(f"{BASE_URL}/api/v1/sales-returns/")
    if response.status_code == 200:
        returns = response.json()
        for ret in returns:
            movements['sales_return'].append({
                'id': ret['return_id'],
                'date': ret['return_date'],
                'product': ret['product_name'],
                'quantity': ret['quantity_returned'],
                'reference': ret['reference_number']
            })
    
    # Get stock adjustments
    response = requests.get(f"{BASE_URL}/api/v1/stock-adjustments/")
    if response.status_code == 200:
        adjustments = response.json()
        for adj in adjustments:
            movements[adj['adjustment_type']].append({
                'id': adj['adjustment_id'],
                'date': adj['adjustment_date'],
                'product': adj['product_name'],
                'quantity': adj['quantity_adjusted'],
                'reference': adj['reference_number']
            })
    
    return movements

def main():
    print("Inventory Movements Verification")
    print("=" * 50)
    
    movements = get_movements()
    
    if not movements:
        print("No movements found!")
        return
    
    total_movements = 0
    
    for movement_type, items in movements.items():
        print(f"\n{movement_type.upper()} ({len(items)} records)")
        print("-" * 40)
        
        for item in items:
            print(f"  ID: {item['id']} | {item['date'][:10]} | {item['product']} | Qty: {item['quantity']} | Ref: {item['reference']}")
            total_movements += 1
    
    print(f"\n{'=' * 50}")
    print(f"Total Movements Created: {total_movements}")
    print(f"Movement Types: {', '.join(movements.keys())}")
    
    # Summary
    print(f"\nSummary:")
    print(f"✅ Sales Returns: {len(movements.get('sales_return', []))}")
    print(f"✅ Stock Damage: {len(movements.get('stock_damage', []))}")
    print(f"✅ Stock Count: {len(movements.get('stock_count', []))}")
    print(f"✅ Stock Expiry: {len(movements.get('stock_expiry', []))}")

if __name__ == "__main__":
    main()