#!/usr/bin/env python3
"""
Quick test for optimizer - avoids terminal issues
"""

import sys
import os
import json
from pathlib import Path

def test_basic_functionality():
    """Test basic optimizer functionality"""
    print("🧪 Testing Optimizer Basic Functionality...")
    
    try:
        # Test 1: Import required modules
        print("1. Testing imports...")
        import optuna
        import backtrader as bt
        import pandas as pd
        print(f"   ✅ Optuna: {optuna.__version__}")
        print(f"   ✅ Backtrader: {bt.__version__}")
        print(f"   ✅ Pandas: {pd.__version__}")
        
        # Test 2: Load parameter spaces
        print("2. Testing parameter spaces...")
        with open("param_spaces_example.json", 'r') as f:
            spaces = json.load(f)
        print(f"   ✅ Loaded {len(spaces)} strategy configurations")
        
        # Test 3: Load test config
        print("3. Testing configuration...")
        with open("configs/config_optimization_test.json", 'r') as f:
            config = json.load(f)
        print(f"   ✅ Config loaded: {config['strategy']}")
        
        # Test 4: Check data file
        print("4. Testing data file...")
        data_file = config['data_file']
        if Path(data_file).exists():
            print(f"   ✅ Data file exists: {data_file}")
        else:
            print(f"   ❌ Data file missing: {data_file}")
            return False
        
        # Test 5: Import optimizer
        print("5. Testing optimizer import...")
        from parameter_optimizer import ParameterOptimizer
        print("   ✅ ParameterOptimizer imported successfully")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_optimization():
    """Test a very simple optimization"""
    print("\n🚀 Testing Simple Optimization...")
    
    try:
        from parameter_optimizer import ParameterOptimizer
        
        # Create optimizer with minimal settings
        optimizer = ParameterOptimizer(
            config_path="configs/config_optimization_test.json",
            strategy_name="VolatilityBreakoutStrategy",
            param_spaces={
                "lookback": {"type": "int", "low": 15, "high": 20},
                "multiplier": {"type": "float", "low": 2.0, "high": 2.5}
            },
            output_dir="reports/optuna_test",
            metric="rmd"
        )
        
        print("   ✅ Optimizer created successfully")
        
        # Run just 2 trials for testing
        study = optimizer.optimize(n_trials=2, n_jobs=1)
        
        print(f"   ✅ Optimization completed: {len(study.trials)} trials")
        print(f"   📊 Best value: {study.best_value:.4f}")
        print(f"   🎯 Best params: {study.best_params}")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 OPTIMIZER QUICK TEST")
    print("=" * 60)
    
    # Test basic functionality
    basic_ok = test_basic_functionality()
    
    if basic_ok:
        # Test simple optimization
        opt_ok = test_simple_optimization()
        
        if opt_ok:
            print("\n🎉 ALL TESTS PASSED! Optimizer is ready to use.")
            print("\n📋 Next steps:")
            print("1. Run full optimization: python run_optimization.py")
            print("2. Check results in reports/optuna_test/")
        else:
            print("\n❌ Optimization test failed")
    else:
        print("\n❌ Basic functionality test failed")
    
    print("=" * 60)
