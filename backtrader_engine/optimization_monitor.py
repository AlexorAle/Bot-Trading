"""
Optimization Monitor - Integration with monitoring system
Tracks optimization progress and results in real-time
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import optuna

from monitoring.bot_monitor import get_monitor

class OptimizationMonitor:
    """Monitor optimization progress and integrate with monitoring system"""
    
    def __init__(self, study_name: str, strategy_name: str, output_dir: str):
        self.study_name = study_name
        self.strategy_name = strategy_name
        self.output_dir = Path(output_dir)
        self.monitor = get_monitor()
        
        # Register optimization as a "bot"
        self.monitor.register_bot(
            bot_id=f"optimizer_{study_name}",
            bot_type="optimization",
            config={
                "strategy": strategy_name,
                "study_name": study_name,
                "output_dir": str(output_dir)
            }
        )
        
        self.best_value = float('-inf')
        self.trial_count = 0
        self.start_time = time.time()
        
        print(f"[OPTIMIZATION MONITOR] Registered optimization: {study_name}")
    
    def update_trial(self, trial: optuna.Trial, objective_value: float):
        """Update monitoring with trial results"""
        self.trial_count += 1
        
        # Update best value if improved
        if objective_value > self.best_value:
            self.best_value = objective_value
            
            # Update bot status with best results
            self.monitor.update_bot_status(
                bot_id=f"optimizer_{self.study_name}",
                status="running",
                equity=objective_value,
                trades=self.trial_count,
                positions=1  # Currently optimizing
            )
            
            # Update strategy metrics
            sharpe = trial.user_attrs.get('sharpe', 0.0)
            total_return = trial.user_attrs.get('total_return', 0.0)
            max_drawdown = trial.user_attrs.get('max_drawdown', 0.0)
            
            self.monitor.update_strategy_metrics(
                strategy_name=self.strategy_name,
                symbol="OPTIMIZATION",
                equity=objective_value,
                pnl=total_return,
                trades=self.trial_count,
                win_rate=1.0 if objective_value > 0 else 0.0
            )
            
            print(f"[OPTIMIZATION MONITOR] New best: {objective_value:.4f} (Trial {trial.number})")
    
    def finalize_optimization(self, study: optuna.Study):
        """Finalize optimization and save monitoring data"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Update final status
        self.monitor.update_bot_status(
            bot_id=f"optimizer_{self.study_name}",
            status="completed",
            equity=study.best_value,
            trades=len(study.trials),
            positions=0
        )
        
        # Save optimization summary
        summary = {
            "study_name": self.study_name,
            "strategy": self.strategy_name,
            "best_value": study.best_value,
            "best_trial": study.best_trial.number,
            "total_trials": len(study.trials),
            "duration_seconds": duration,
            "trials_per_minute": len(study.trials) / (duration / 60),
            "completed_at": datetime.now().isoformat()
        }
        
        summary_file = self.output_dir / "optimization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[OPTIMIZATION MONITOR] Completed: {len(study.trials)} trials in {duration:.2f}s")
        print(f"[OPTIMIZATION MONITOR] Best value: {study.best_value:.4f}")
        print(f"[OPTIMIZATION MONITOR] Summary saved to: {summary_file}")

def create_optimization_monitor(study_name: str, strategy_name: str, output_dir: str) -> OptimizationMonitor:
    """Create and return optimization monitor instance"""
    return OptimizationMonitor(study_name, strategy_name, output_dir)
