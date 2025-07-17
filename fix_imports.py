#!/usr/bin/env python3
"""
Fix all schema imports after renaming schemas.py to base_schemas.py
This is how companies that scale handle refactoring
"""
import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix various import patterns
    replacements = [
        # from ..schemas import X
        (r'from \.\.schemas import', 'from ..base_schemas import'),
        # from api.schemas import X  
        (r'from api\.schemas import', 'from api.base_schemas import'),
        # import api.schemas
        (r'import api\.schemas\b', 'import api.base_schemas'),
        # from . import schemas
        (r'from \. import schemas\b', 'from . import base_schemas'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Only write if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Fixed imports in: {filepath}")
        return True
    return False

def main():
    """Fix all Python files in the api directory"""
    print("🔧 Fixing schema imports...")
    print("=" * 50)
    
    fixed_count = 0
    checked_count = 0
    
    for root, dirs, files in os.walk('api'):
        # Skip __pycache__ directories
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                checked_count += 1
                
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print("=" * 50)
    print(f"✅ Fixed {fixed_count} files out of {checked_count} checked")
    print("\n💡 This is exactly how companies that scale handle refactoring:")
    print("   1. Identify the problem pattern")
    print("   2. Write a script to fix it everywhere") 
    print("   3. Test the changes")
    print("   4. Deploy with confidence")

if __name__ == "__main__":
    main()