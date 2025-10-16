#!/usr/bin/env python3
"""
Final Optimization Runner - Robust execution
Handles terminal issues and executes optimization reliably
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

def run_optimization_final():
    """Run optimization with robust error handling"""
    
    print("🚀 FINAL OPTIMIZATION RUNNER")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("parameter_optimizer.py").exists():
        print("❌ parameter_optimizer.py not found")
        return False
    
    # Try to install dependencies if needed
    print("📦 Checking dependencies...")
    try:
        import optuna
        import backtrader as bt
        print(f"✅ Dependencies OK - Optuna: {optuna.__version__}")
    except ImportError:
        print("📦 Installing dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "optuna", "backtrader"], 
                         check=True, capture_output=True)
            print("✅ Dependencies installed")
        except:
            print("❌ Could not install dependencies")
            return False
    
    # Create output directory
    output_dir = Path("reports/optuna_final")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    
    # Load configuration
    try:
        with open("configs/config_optimization_real.json", 'r') as f:
            config = json.load(f)
        print(f"✅ Config loaded: {config['strategy']}")
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False
    
    # Load parameter spaces
    try:
        with open("param_spaces_example.json", 'r') as f:
            param_spaces = json.load(f)
        print(f"✅ Parameter spaces loaded")
    except Exception as e:
        print(f"❌ Parameter spaces error: {e}")
        return False
    
    # Check data file
    data_file = config['data_file']
    if not Path(data_file).exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    print(f"✅ Data file found: {data_file}")
    
    # Import and run optimizer
    try:
        from parameter_optimizer import ParameterOptimizer
        
        print("🔄 Creating optimizer...")
        optimizer = ParameterOptimizer(
            config_path="configs/config_optimization_real.json",
            strategy_name="VolatilityBreakoutStrategy",
            param_spaces=param_spaces["VolatilityBreakoutStrategy"],
            output_dir=str(output_dir),
            metric="rmd"
        )
        
        print("✅ Optimizer created successfully")
        print("🔄 Running optimization (150 trials)...")
        print("⏳ This may take 30-60 minutes...")
        
        start_time = time.time()
        
        # Run optimization
        study = optimizer.optimize(n_trials=150, n_jobs=1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("🎉 OPTIMIZATION COMPLETED!")
        print("=" * 60)
        print(f"⏱️  Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        print(f"📊 Trials completed: {len(study.trials)}")
        print(f"🎯 Best RMD: {study.best_value:.4f}")
        print(f"🏆 Best trial: #{study.best_trial.number}")
        
        # Show best parameters
        print("\n🎯 BEST PARAMETERS:")
        for param, value in study.best_params.items():
            print(f"   {param}: {value}")
        
        # Show performance metrics
        best_trial = study.best_trial
        sharpe = best_trial.user_attrs.get('sharpe', 0.0)
        total_return = best_trial.user_attrs.get('total_return', 0.0)
        max_drawdown = best_trial.user_attrs.get('max_drawdown', 0.0)
        
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"   RMD (Return/MaxDD): {study.best_value:.4f}")
        print(f"   Sharpe Ratio: {sharpe:.4f}")
        print(f"   Total Return: {total_return:.4f} ({total_return*100:.2f}%)")
        print(f"   Max Drawdown: {max_drawdown:.4f} ({max_drawdown*100:.2f}%)")
        
        # Show top 5 trials
        print(f"\n🏅 TOP 5 TRIALS:")
        sorted_trials = sorted(study.trials, key=lambda t: t.value or float('-inf'), reverse=True)
        for i, trial in enumerate(sorted_trials[:5]):
            if trial.value is not None:
                print(f"   #{i+1}. Trial {trial.number}: RMD={trial.value:.4f}, "
                      f"Sharpe={trial.user_attrs.get('sharpe', 0.0):.4f}")
        
        # Save comprehensive summary
        summary = {
            "optimization_completed": True,
            "strategy": "VolatilityBreakoutStrategy",
            "data_period": "2024-01-01 to 2025-01-01",
            "trials": len(study.trials),
            "duration_seconds": duration,
            "duration_minutes": duration/60,
            "best_rmd": study.best_value,
            "best_trial": study.best_trial.number,
            "best_params": study.best_params,
            "performance": {
                "rmd": study.best_value,
                "sharpe": sharpe,
                "total_return": total_return,
                "max_drawdown": max_drawdown
            },
            "top_5_trials": [
                {
                    "rank": i+1,
                    "trial_number": trial.number,
                    "rmd": trial.value,
                    "sharpe": trial.user_attrs.get('sharpe', 0.0),
                    "params": trial.params
                }
                for i, trial in enumerate(sorted_trials[:5])
                if trial.value is not None
            ],
            "completed_at": datetime.now().isoformat()
        }
        
        summary_file = output_dir / "optimization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Summary saved to: {summary_file}")
        print(f"📁 Full results in: {optimizer.study_dir}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_optimization_final()
    
    if success:
        print("\n🎉 REAL OPTIMIZATION COMPLETED SUCCESSFULLY!")
        print("📋 Next steps:")
        print("1. Review results in reports/optuna_final/")
        print("2. Analyze best parameters")
        print("3. Test optimized parameters in backtesting")
        print("4. Proceed to Step 3: Walk-forward testing")
    else:
        print("\n❌ Optimization failed. Please check errors above.")
    
    sys.exit(0 if success else 1)
