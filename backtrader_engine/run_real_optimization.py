#!/usr/bin/env python3
"""
Real Optimization Runner - 100-200 trials
Executes serious parameter optimization with comprehensive settings
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

def run_real_optimization():
    """Run real parameter optimization with 150 trials"""
    
    print("🚀 Starting REAL Parameter Optimization...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("parameter_optimizer.py").exists():
        print("❌ parameter_optimizer.py not found. Please run from backtrader_engine directory.")
        return False
    
    # Check dependencies
    try:
        import optuna
        import backtrader as bt
        print(f"✅ Dependencies OK - Optuna: {optuna.__version__}, Backtrader: {bt.__version__}")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install optuna backtrader")
        return False
    
    # Create output directory
    output_dir = Path("reports/optuna_real")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define optimization command for real optimization
    cmd = [
        "python", "parameter_optimizer.py",
        "--config", "configs/config_optimization_real.json",
        "--strategy", "VolatilityBreakoutStrategy", 
        "--trials", "150",  # Real optimization with 150 trials
        "--metric", "rmd",   # Return/MaxDD ratio
        "--spaces", "param_spaces_example.json",
        "--output-dir", str(output_dir),
        "--n-jobs", "1"     # Single job for stability
    ]
    
    print(f"📋 Configuration:")
    print(f"   Strategy: VolatilityBreakoutStrategy")
    print(f"   Data: BTC/USDT 15min (2024-01-01 to 2025-01-01)")
    print(f"   Trials: 150")
    print(f"   Metric: RMD (Return/MaxDD)")
    print(f"   Output: {output_dir}")
    print(f"   Command: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = time.time()
    print(f"⏳ Starting optimization at {datetime.now().strftime('%H:%M:%S')}...")
    
    try:
        # Import and run optimizer directly
        from parameter_optimizer import ParameterOptimizer
        
        # Load parameter spaces
        with open("param_spaces_example.json", 'r') as f:
            param_spaces = json.load(f)
        
        # Create optimizer
        optimizer = ParameterOptimizer(
            config_path="configs/config_optimization_real.json",
            strategy_name="VolatilityBreakoutStrategy",
            param_spaces=param_spaces["VolatilityBreakoutStrategy"],
            output_dir=str(output_dir),
            metric="rmd"
        )
        
        print("✅ Optimizer created successfully")
        print("🔄 Running optimization...")
        
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
        print(f"📁 Results saved to: {optimizer.study_dir}")
        
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
        
        # Save summary
        summary = {
            "optimization_completed": True,
            "strategy": "VolatilityBreakoutStrategy",
            "data_period": "2024-01-01 to 2025-01-01",
            "trials": len(study.trials),
            "duration_seconds": duration,
            "best_rmd": study.best_value,
            "best_trial": study.best_trial.number,
            "best_params": study.best_params,
            "performance": {
                "rmd": study.best_value,
                "sharpe": sharpe,
                "total_return": total_return,
                "max_drawdown": max_drawdown
            },
            "completed_at": datetime.now().isoformat()
        }
        
        summary_file = output_dir / "optimization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Summary saved to: {summary_file}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_real_optimization()
    
    if success:
        print("\n🎉 REAL OPTIMIZATION COMPLETED SUCCESSFULLY!")
        print("📋 Next steps:")
        print("1. Review results in reports/optuna_real/")
        print("2. Analyze best parameters")
        print("3. Test optimized parameters in backtesting")
        print("4. Proceed to Step 3: Walk-forward testing")
    else:
        print("\n❌ Optimization failed. Please check errors above.")
    
    sys.exit(0 if success else 1)
