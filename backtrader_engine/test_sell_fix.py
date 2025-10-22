import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from exchanges.bybit_paper_trader import PaperPosition
from risk_manager import RiskManager

print('Testing SELL signals for all symbols...')

config = {'risk_limits': {'max_position_size': 0.1, 'min_confidence': 0.6, 'max_volatility': 0.05}}
risk_manager = RiskManager(config)

symbols = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT']
all_passed = True

for symbol in symbols:
    print(f'Testing {symbol}...')
    
    positions = {
        symbol: PaperPosition(symbol=symbol, side='Buy', size=0.1, entry_price=1000.0, mark_price=1050.0)
    }
    
    signal_data = {
        'symbol': symbol,
        'signal_type': 'Sell',
        'confidence': 0.8,
        'price': 1100.0,
        'strategy': 'TestStrategy'
    }
    
    market_data = {
        'price': 1100.0,
        'atr': 10.0,
        'volume': 1000000,
        'volume_avg': 1000000,
        'adx': 30.0,
        'rsi': 60.0,
        'volatility': 0.02
    }
    
    try:
        is_valid, reason = risk_manager.validate_signal(
            signal_data=signal_data,
            current_balance=10000.0,
            current_positions=positions,
            market_data=market_data
        )
        
        if is_valid:
            print(f' {symbol} PASSED: {reason}')
        else:
            print(f' {symbol} FAILED: {reason}')
            all_passed = False
            
    except Exception as e:
        print(f' {symbol} EXCEPTION: {e}')
        all_passed = False

print('Overall result: ALL PASSED' if all_passed else 'Overall result: SOME FAILED')
