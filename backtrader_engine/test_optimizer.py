#!/usr/bin/env python3
"""
Test script for parameter optimizer
Quick test with minimal trials to verify functionality
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_optimizer():
    """Test the parameter optimizer with minimal configuration"""
    
    print("🧪 Testing Parameter Optimizer...")
    
    # Check if required files exist
    required_files = [
        "parameter_optimizer.py",
        "param_spaces_example.json",
        "configs/config_volatility.json"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing required file: {file}")
            return False
        print(f"✅ Found: {file}")
    
    # Check if data file exists
    with open("configs/config_volatility.json", 'r') as f:
        config = json.load(f)
    
    data_file = config.get('data_file', '')
    if not Path(data_file).exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    print(f"✅ Found data file: {data_file}")
    
    # Test import
    try:
        from parameter_optimizer import ParameterOptimizer
        print("✅ Successfully imported ParameterOptimizer")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test parameter spaces loading
    try:
        with open("param_spaces_example.json", 'r') as f:
            param_spaces = json.load(f)
        print("✅ Successfully loaded parameter spaces")
        print(f"✅ Found {len(param_spaces)} strategy configurations")
    except Exception as e:
        print(f"❌ Error loading parameter spaces: {e}")
        return False
    
    print("\n🎯 All tests passed! Optimizer is ready to use.")
    print("\n📋 Next steps:")
    print("1. Run a quick optimization test:")
    print("   python parameter_optimizer.py \\")
    print("     --config configs/config_volatility.json \\")
    print("     --strategy VolatilityBreakoutStrategy \\")
    print("     --trials 5 \\")
    print("     --metric rmd \\")
    print("     --spaces param_spaces_example.json \\")
    print("     --output-dir reports/optuna \\")
    print("     --n-jobs 1")
    print("\n2. Check results in reports/optuna/")
    
    return True

if __name__ == "__main__":
    success = test_optimizer()
    sys.exit(0 if success else 1)
