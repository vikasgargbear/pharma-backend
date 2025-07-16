#!/usr/bin/env python3
"""
Test runner script for the Pharma ERP system
Runs the complete test suite with coverage reporting
"""
import subprocess
import sys
import os

def run_tests():
    """Run the complete test suite"""
    print("🧪 Running Pharma ERP Test Suite...")
    print("=" * 50)
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--verbose",
            "--cov=api",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=70",  # Start with 70% target
            "tests/"
        ], check=True)
        
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("pip install -r requirements.txt")
        return False

def run_specific_test(test_path):
    """Run a specific test file or test function"""
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--verbose",
            test_path
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        print(f"🧪 Running specific test: {test_path}")
        success = run_specific_test(test_path)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1)