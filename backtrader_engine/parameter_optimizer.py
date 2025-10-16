#!/usr/bin/env python3
"""
Parameter Optimizer with Optuna
Bayesian optimization for trading strategy parameters

Usage:
    python parameter_optimizer.py \
        --config backtrader_engine/configs/config_btc_24months.json \
        --strategy VolatilityBreakoutStrategy \
        --trials 60 \
        --metric rmd \
        --spaces param_spaces_example.json \
        --output-dir backtrader_engine/reports/optuna \
        --n-jobs 1
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import traceback

import optuna
import pandas as pd
import backtrader as bt
from backtrader import Analyzer

# Add current directory to path for strategy imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ReturnMaxDrawdownAnalyzer(Analyzer):
    """Custom analyzer for Return/MaxDD ratio"""
    
    def __init__(self):
        self.returns = []
        self.drawdowns = []
        
    def next(self):
        """Called on each bar"""
        current_value = self.broker.getvalue()
        if hasattr(self, 'last_value'):
            ret = (current_value - self.last_value) / self.last_value
            self.returns.append(ret)
            
            # Calculate drawdown
            if not hasattr(self, 'peak_value'):
                self.peak_value = current_value
            
            if current_value > self.peak_value:
                self.peak_value = current_value
            
            dd = (self.peak_value - current_value) / self.peak_value
            self.drawdowns.append(dd)
        
        self.last_value = current_value
    
    def get_analysis(self):
        """Return analysis results"""
        if not self.returns or not self.drawdowns:
            return {'rmd': 0.0, 'sharpe': 0.0, 'total_return': 0.0, 'max_drawdown': 0.0}
        
        total_return = (self.last_value - self.broker.startingcash) / self.broker.startingcash
        max_drawdown = max(self.drawdowns) if self.drawdowns else 0.0
        
        # Calculate Sharpe ratio (simplified)
        if len(self.returns) > 1:
            mean_return = sum(self.returns) / len(self.returns)
            std_return = (sum((r - mean_return) ** 2 for r in self.returns) / len(self.returns)) ** 0.5
            sharpe = mean_return / std_return if std_return > 0 else 0.0
        else:
            sharpe = 0.0
        
        # Return/MaxDD ratio
        rmd = total_return / max_drawdown if max_drawdown > 0 else 0.0
        
        return {
            'rmd': rmd,
            'sharpe': sharpe,
            'total_return': total_return,
            'max_drawdown': max_drawdown
        }

class ParameterOptimizer:
    """Bayesian parameter optimizer using Optuna"""
    
    def __init__(self, config_path: str, strategy_name: str, param_spaces: Dict, 
                 output_dir: str, metric: str = 'rmd'):
        self.config_path = config_path
        self.strategy_name = strategy_name
        self.param_spaces = param_spaces
        self.output_dir = output_dir
        self.metric = metric
        
        # Load configuration
        self.config = self._load_config()
        
        # Load strategy class
        self.strategy_class = self._load_strategy()
        
        # Create output directory
        self.study_name = f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.study_dir = Path(output_dir) / self.study_name
        self.study_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[OPTIMIZER] Initialized for {strategy_name}")
        print(f"[OPTIMIZER] Config: {config_path}")
        print(f"[OPTIMIZER] Output: {self.study_dir}")
        print(f"[OPTIMIZER] Metric: {metric}")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        print(f"[CONFIG] Loaded config from {self.config_path}")
        print(f"[CONFIG] Data file: {config.get('data_file', 'N/A')}")
        print(f"[CONFIG] Date range: {config.get('start_date', 'N/A')} to {config.get('end_date', 'N/A')}")
        
        return config
    
    def _load_strategy(self):
        """Load strategy class dynamically"""
        # Try different import patterns
        import_patterns = [
            f"strategies.{self.strategy_name.lower()}.{self.strategy_name}",
            f"strategies.{self.strategy_name.lower()}",
            f"{self.strategy_name.lower()}.{self.strategy_name}",
            self.strategy_name
        ]
        
        for pattern in import_patterns:
            try:
                if '.' in pattern:
                    module_name, class_name = pattern.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)
                    print(f"[STRATEGY] Loaded {self.strategy_name} from {pattern}")
                    return strategy_class
                else:
                    # Direct class name
                    strategy_class = globals()[pattern]
                    print(f"[STRATEGY] Loaded {self.strategy_name} directly")
                    return strategy_class
            except (ImportError, AttributeError, KeyError):
                continue
        
        raise ImportError(f"Could not import strategy: {self.strategy_name}")
    
    def _create_cerebro(self, params: Dict) -> bt.Cerebro:
        """Create and configure Cerebro instance"""
        cerebro = bt.Cerebro()
        
        # Add data
        data = bt.feeds.GenericCSVData(
            dataname=self.config['data_file'],
            datetime=0,
            open=1,
            high=2,
            low=3,
            close=4,
            volume=5,
            dtformat='%Y-%m-%d %H:%M:%S',
            timeframe=bt.TimeFrame.Minutes,
            compression=15
        )
        
        # Filter data by date range
        if 'start_date' in self.config and 'end_date' in self.config:
            data = bt.indicators.TimeFilter(data, 
                                          fromdate=datetime.strptime(self.config['start_date'], '%Y-%m-%d'),
                                          todate=datetime.strptime(self.config['end_date'], '%Y-%m-%d'))
        
        cerebro.adddata(data)
        
        # Add strategy with optimized parameters
        strategy_params = self._merge_params(params)
        cerebro.addstrategy(self.strategy_class, **strategy_params)
        
        # Set broker parameters
        cerebro.broker.setcash(self.config.get('initial_cash', 10000))
        cerebro.broker.setcommission(commission=self.config.get('commission', 0.001))
        
        # Add analyzers
        cerebro.addanalyzer(ReturnMaxDrawdownAnalyzer, _name='rmd_analyzer')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        return cerebro
    
    def _merge_params(self, optuna_params: Dict) -> Dict:
        """Merge Optuna parameters with config parameters"""
        merged = self.config.copy()
        
        # Remove non-strategy parameters
        non_strategy_params = ['strategy', 'symbol', 'data_file', 'timeframe', 
                              'commission', 'initial_cash', 'start_date', 'end_date']
        for param in non_strategy_params:
            merged.pop(param, None)
        
        # Add Optuna parameters
        merged.update(optuna_params)
        
        return merged
    
    def _objective(self, trial) -> float:
        """Objective function for Optuna optimization"""
        try:
            # Sample parameters from search space
            params = {}
            for param_name, param_config in self.param_spaces.items():
                if param_config['type'] == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name, 
                        param_config['low'], 
                        param_config['high']
                    )
                elif param_config['type'] == 'float':
                    params[param_name] = trial.suggest_float(
                        param_name, 
                        param_config['low'], 
                        param_config['high']
                    )
                elif param_config['type'] == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name, 
                        param_config['choices']
                    )
            
            # Create and run backtest
            cerebro = self._create_cerebro(params)
            results = cerebro.run()
            
            # Extract results
            strategy_result = results[0]
            rmd_analysis = strategy_result.analyzers.rmd_analyzer.get_analysis()
            
            # Set user attributes for additional metrics
            trial.set_user_attr('sharpe', rmd_analysis['sharpe'])
            trial.set_user_attr('total_return', rmd_analysis['total_return'])
            trial.set_user_attr('max_drawdown', rmd_analysis['max_drawdown'])
            
            # Return objective metric
            objective_value = rmd_analysis[self.metric]
            
            print(f"[TRIAL {trial.number}] {self.metric}: {objective_value:.4f}, "
                  f"Sharpe: {rmd_analysis['sharpe']:.4f}, "
                  f"Return: {rmd_analysis['total_return']:.4f}, "
                  f"MaxDD: {rmd_analysis['max_drawdown']:.4f}")
            
            return objective_value
            
        except Exception as e:
            print(f"[TRIAL {trial.number}] ERROR: {str(e)}")
            traceback.print_exc()
            return float('-inf')
    
    def optimize(self, n_trials: int, n_jobs: int = 1) -> optuna.Study:
        """Run optimization"""
        print(f"[OPTIMIZATION] Starting optimization with {n_trials} trials")
        print(f"[OPTIMIZATION] Parallel jobs: {n_jobs}")
        
        # Create study
        study = optuna.create_study(
            direction='maximize',
            study_name=self.study_name,
            storage=f"sqlite:///{self.study_dir}/study.db"
        )
        
        # Run optimization
        study.optimize(self._objective, n_trials=n_trials, n_jobs=n_jobs)
        
        # Save results
        self._save_results(study)
        
        return study
    
    def _save_results(self, study: optuna.Study):
        """Save optimization results"""
        # Best parameters
        best_params = study.best_params.copy()
        best_params['objective_value'] = study.best_value
        best_params['sharpe'] = study.best_trial.user_attrs.get('sharpe', 0.0)
        best_params['total_return'] = study.best_trial.user_attrs.get('total_return', 0.0)
        best_params['max_drawdown'] = study.best_trial.user_attrs.get('max_drawdown', 0.0)
        
        with open(self.study_dir / 'best_params.json', 'w') as f:
            json.dump(best_params, f, indent=2)
        
        # All trials
        trials_data = []
        for trial in study.trials:
            trial_data = {
                'number': trial.number,
                'value': trial.value,
                'params': trial.params,
                'sharpe': trial.user_attrs.get('sharpe', 0.0),
                'total_return': trial.user_attrs.get('total_return', 0.0),
                'max_drawdown': trial.user_attrs.get('max_drawdown', 0.0),
                'state': trial.state.name
            }
            trials_data.append(trial_data)
        
        trials_df = pd.DataFrame(trials_data)
        trials_df.to_csv(self.study_dir / 'trials.csv', index=False)
        
        # Study summary
        summary = {
            'study_name': self.study_name,
            'strategy': self.strategy_name,
            'config_file': self.config_path,
            'n_trials': len(study.trials),
            'best_value': study.best_value,
            'best_params': study.best_params,
            'best_trial_number': study.best_trial.number,
            'optimization_direction': study.direction.name,
            'created_at': datetime.now().isoformat()
        }
        
        with open(self.study_dir / 'study_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"[RESULTS] Saved to {self.study_dir}")
        print(f"[RESULTS] Best {self.metric}: {study.best_value:.4f}")
        print(f"[RESULTS] Best trial: {study.best_trial.number}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Parameter Optimizer with Optuna')
    parser.add_argument('--config', required=True, help='Configuration JSON file')
    parser.add_argument('--strategy', required=True, help='Strategy class name')
    parser.add_argument('--trials', type=int, default=100, help='Number of trials')
    parser.add_argument('--metric', default='rmd', choices=['rmd', 'sharpe', 'total_return'], 
                       help='Optimization metric')
    parser.add_argument('--spaces', required=True, help='Parameter spaces JSON file')
    parser.add_argument('--output-dir', default='reports/optuna', help='Output directory')
    parser.add_argument('--n-jobs', type=int, default=1, help='Number of parallel jobs')
    
    args = parser.parse_args()
    
    # Load parameter spaces
    with open(args.spaces, 'r') as f:
        param_spaces = json.load(f)
    
    # Create optimizer
    optimizer = ParameterOptimizer(
        config_path=args.config,
        strategy_name=args.strategy,
        param_spaces=param_spaces,
        output_dir=args.output_dir,
        metric=args.metric
    )
    
    # Run optimization
    start_time = time.time()
    study = optimizer.optimize(n_trials=args.trials, n_jobs=args.n_jobs)
    end_time = time.time()
    
    print(f"\n[COMPLETED] Optimization finished in {end_time - start_time:.2f} seconds")
    print(f"[COMPLETED] Best {args.metric}: {study.best_value:.4f}")
    print(f"[COMPLETED] Best parameters: {study.best_params}")

if __name__ == '__main__':
    main()
