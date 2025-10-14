#!/usr/bin/env python3
"""
Smoke Test Script for Individual Strategies
Tests problematic strategies with 14-day periods
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from portfolio_engine import PortfolioEngine

def load_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config {config_path}: {e}")
        return None

def run_smoke_test():
    """Run smoke tests for problematic strategies"""
    
    # Create engine
    engine = PortfolioEngine(enable_regime_detection=False, enable_risk_parity=False, enable_strategy_handle=False)
    
    # Configure dates for 14-day smoke test
    end_date = datetime(2025, 10, 9)
    start_date = end_date - timedelta(days=14)
    
    print(f'🔥 SMOKE TEST - 14 días: {start_date.date()} a {end_date.date()}')
    print("=" * 60)
    
    # Test RSIEMAMomentumStrategy
    print('\n📊 TESTING RSIEMAMomentumStrategy...')
    config_rsi = load_config('configs/config_rsi_ema.json')
    if config_rsi:
        config_rsi['start_date'] = start_date.strftime('%Y-%m-%d')
        config_rsi['end_date'] = end_date.strftime('%Y-%m-%d')
    else:
        print('❌ Error loading RSI config')
        return
    
    try:
        result_rsi = engine.run_single_strategy('RSIEMAMomentumStrategy', 'BTCUSDT', 'data/BTCUSDT_15min.csv', config_rsi)
        print(f'✅ RSIEMAMomentumStrategy: {result_rsi.get("total_return", "N/A")}% return, {result_rsi.get("total_trades", 0)} trades')
        if result_rsi.get('error'):
            print(f'⚠️  RSIEMAMomentumStrategy WARNING: {result_rsi["error"]}')
    except Exception as e:
        print(f'❌ RSIEMAMomentumStrategy ERROR: {e}')
    
    # Test EMABreakoutConservativeStrategy  
    print('\n📊 TESTING EMABreakoutConservativeStrategy...')
    config_ema = load_config('configs/config_ema_breakout_conservative.json')
    if config_ema:
        config_ema['start_date'] = start_date.strftime('%Y-%m-%d')
        config_ema['end_date'] = end_date.strftime('%Y-%m-%d')
    else:
        print('❌ Error loading EMA config')
        return
    
    try:
        result_ema = engine.run_single_strategy('EMABreakoutConservativeStrategy', 'BTCUSDT', 'data/BTCUSDT_15min.csv', config_ema)
        print(f'✅ EMABreakoutConservativeStrategy: {result_ema.get("total_return", "N/A")}% return, {result_ema.get("total_trades", 0)} trades')
        if result_ema.get('error'):
            print(f'⚠️  EMABreakoutConservativeStrategy WARNING: {result_ema["error"]}')
    except Exception as e:
        print(f'❌ EMABreakoutConservativeStrategy ERROR: {e}')
    
    print('\n🎯 SMOKE TEST COMPLETED')

if __name__ == "__main__":
    run_smoke_test()
