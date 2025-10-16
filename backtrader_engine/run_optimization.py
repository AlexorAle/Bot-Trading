#!/usr/bin/env python3
"""
Quick optimization runner
Executes parameter optimization with predefined settings
"""

import os
import sys
import subprocess
from pathlib import Path

def run_optimization():
    """Run parameter optimization with test settings"""
    
    print("🚀 Starting Parameter Optimization...")
    
    # Check if we're in the right directory
    if not Path("parameter_optimizer.py").exists():
        print("❌ parameter_optimizer.py not found. Please run from backtrader_engine directory.")
        return False
    
    # Define optimization command
    cmd = [
        "python", "parameter_optimizer.py",
        "--config", "configs/config_optimization_test.json",
        "--strategy", "VolatilityBreakoutStrategy", 
        "--trials", "10",  # Small number for testing
        "--metric", "rmd",
        "--spaces", "param_spaces_example.json",
        "--output-dir", "reports/optuna",
        "--n-jobs", "1"
    ]
    
    print(f"📋 Command: {' '.join(cmd)}")
    print("⏳ Starting optimization...")
    
    try:
        # Run optimization
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Optimization completed successfully!")
            print("\n📊 Results:")
            print(result.stdout)
            
            # Check if results were created
            results_dir = Path("reports/optuna")
            if results_dir.exists():
                study_dirs = list(results_dir.glob("VolatilityBreakoutStrategy_*"))
                if study_dirs:
                    latest_study = max(study_dirs, key=lambda x: x.stat().st_mtime)
                    print(f"\n📁 Results saved to: {latest_study}")
                    
                    # Show best parameters
                    best_params_file = latest_study / "best_params.json"
                    if best_params_file.exists():
                        import json
                        with open(best_params_file, 'r') as f:
                            best_params = json.load(f)
                        print(f"\n🎯 Best Parameters:")
                        for key, value in best_params.items():
                            if key not in ['objective_value', 'sharpe', 'total_return', 'max_drawdown']:
                                print(f"   {key}: {value}")
                        print(f"\n📈 Performance:")
                        print(f"   RMD: {best_params.get('objective_value', 'N/A'):.4f}")
                        print(f"   Sharpe: {best_params.get('sharpe', 'N/A'):.4f}")
                        print(f"   Return: {best_params.get('total_return', 'N/A'):.4f}")
                        print(f"   Max DD: {best_params.get('max_drawdown', 'N/A'):.4f}")
            
            return True
        else:
            print("❌ Optimization failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Optimization timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running optimization: {e}")
        return False

if __name__ == "__main__":
    success = run_optimization()
    sys.exit(0 if success else 1)
