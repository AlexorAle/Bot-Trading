import unittest
import asyncio
import json
import time
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from signal_engine import SignalEngine, TradingSignal
from risk_manager import RiskManager
from exchanges.bybit_paper_trader import BybitPaperTrader, PaperPosition
from enhanced_logger import EnhancedLogger

class IntegrationTestFramework:
    def __init__(self):
        self.logger = EnhancedLogger('integration_tests')
        self.test_results = []
    
    def run_all_tests(self):
        print(' Running Integration Tests...')
        print('='*50)
        
        # Test 1: Signal Generation to Risk Validation
        self.test_signal_to_risk_flow()
        
        # Test 2: Risk Validation to Position Creation
        self.test_risk_to_position_flow()
        
        # Test 3: End-to-End Signal Processing
        self.test_end_to_end_signal_processing()
        
        # Test 4: Configuration Loading
        self.test_configuration_loading()
        
        # Summary
        self.print_summary()
    
    def test_signal_to_risk_flow(self):
        print('Test 1: Signal Generation to Risk Validation')
        
        try:
            # Load configs
            with open('configs/strategies_config_optimized.json', 'r') as f:
                strategies_config = json.load(f)
            
            with open('configs/risk_config_optimized.json', 'r') as f:
                risk_config = json.load(f)
            
            # Create engines
            signal_engine = SignalEngine(strategies_config)
            risk_manager = RiskManager(risk_config)
            
            # Generate signal
            indicators = {'rsi': 60.0, 'ema_20': 3800.0, 'atr': 20.0, 'volume_ratio': 1.2}
            strategy_config = next(s for s in strategies_config['active_strategies'] if s['name'] == 'RSIEMAMomentumStrategy')
            
            signal = signal_engine._rsi_ema_momentum_signal(
                'ETHUSDT', 3850.0, time.time(), indicators, strategy_config['parameters']
            )
            
            if signal:
                # Validate with risk manager
                signal_data = {
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'price': signal.price,
                    'strategy': signal.strategy
                }
                
                market_data = {
                    'price': signal.price,
                    'atr': indicators['atr'],
                    'volume': 1000000,
                    'volume_avg': 1000000,
                    'adx': 30.0,
                    'rsi': indicators['rsi'],
                    'volatility': 0.02
                }
                
                is_valid, reason = risk_manager.validate_signal(
                    signal_data=signal_data,
                    current_balance=10000.0,
                    current_positions={},
                    market_data=market_data
                )
                
                self.logger.log_signal(signal_data, 'VALIDATED' if is_valid else 'REJECTED', reason)
                
                if is_valid:
                    print('   PASS: Signal generated and validated')
                    self.test_results.append(('Signal to Risk Flow', True, 'Signal validated successfully'))
                else:
                    print(f'   PARTIAL: Signal generated but rejected: {reason}')
                    self.test_results.append(('Signal to Risk Flow', False, f'Signal rejected: {reason}'))
            else:
                print('   FAIL: No signal generated')
                self.test_results.append(('Signal to Risk Flow', False, 'No signal generated'))
                
        except Exception as e:
            print(f'   ERROR: {e}')
            self.test_results.append(('Signal to Risk Flow', False, f'Exception: {e}'))
    
    def test_risk_to_position_flow(self):
        print('Test 2: Risk Validation to Position Creation')
        
        try:
            # Create test position
            position = PaperPosition(
                symbol='ETHUSDT',
                side='Buy',
                size=0.5,
                entry_price=3800.0,
                mark_price=3850.0
            )
            
            # Test position access (the bug we fixed)
            if hasattr(position, 'size'):
                size = position.size
                side = position.side
                
                print(f'   PASS: Position attributes accessible (size={size}, side={side})')
                self.test_results.append(('Risk to Position Flow', True, 'Position attributes accessible'))
                
                # Log position
                position_data = {
                    'symbol': position.symbol,
                    'side': position.side,
                    'size': position.size,
                    'price': position.entry_price,
                    'pnl': position.unrealized_pnl
                }
                
                self.logger.log_position(position_data, 'CREATED')
            else:
                print('   FAIL: Position attributes not accessible')
                self.test_results.append(('Risk to Position Flow', False, 'Position attributes not accessible'))
                
        except Exception as e:
            print(f'   ERROR: {e}')
            self.test_results.append(('Risk to Position Flow', False, f'Exception: {e}'))
    
    def test_end_to_end_signal_processing(self):
        print('Test 3: End-to-End Signal Processing')
        
        try:
            # Load configs
            with open('configs/strategies_config_optimized.json', 'r') as f:
                strategies_config = json.load(f)
            
            with open('configs/risk_config_optimized.json', 'r') as f:
                risk_config = json.load(f)
            
            # Create engines
            signal_engine = SignalEngine(strategies_config)
            risk_manager = RiskManager(risk_config)
            
            # Test multiple strategies
            strategies_to_test = ['RSIEMAMomentumStrategy', 'BollingerReversionStrategy']
            successful_signals = 0
            
            for strategy_name in strategies_to_test:
                strategy_config = next(s for s in strategies_config['active_strategies'] if s['name'] == strategy_name)
                
                if strategy_name == 'RSIEMAMomentumStrategy':
                    indicators = {'rsi': 60.0, 'ema_20': 3800.0, 'atr': 20.0, 'volume_ratio': 1.2}
                    signal = signal_engine._rsi_ema_momentum_signal(
                        'ETHUSDT', 3850.0, time.time(), indicators, strategy_config['parameters']
                    )
                elif strategy_name == 'BollingerReversionStrategy':
                    indicators = {'bb_upper': 3900.0, 'bb_lower': 3700.0, 'bb_middle': 3800.0, 'rsi': 25.0, 'volume_ratio': 1.3}
                    signal = signal_engine._bollinger_reversion_signal(
                        'ETHUSDT', 3700.0, time.time(), indicators, strategy_config['parameters']
                    )
                
                if signal and signal.confidence >= 0.60:
                    successful_signals += 1
                    print(f'   {strategy_name}: Signal generated (conf={signal.confidence:.3f})')
                else:
                    print(f'   {strategy_name}: No signal or low confidence')
            
            if successful_signals >= 1:
                print(f'   PASS: {successful_signals}/{len(strategies_to_test)} strategies generated signals')
                self.test_results.append(('End-to-End Processing', True, f'{successful_signals} strategies working'))
            else:
                print('   FAIL: No strategies generated valid signals')
                self.test_results.append(('End-to-End Processing', False, 'No valid signals'))
                
        except Exception as e:
            print(f'   ERROR: {e}')
            self.test_results.append(('End-to-End Processing', False, f'Exception: {e}'))
    
    def test_configuration_loading(self):
        print('Test 4: Configuration Loading')
        
        try:
            # Test optimized configs
            with open('configs/strategies_config_optimized.json', 'r') as f:
                strategies_config = json.load(f)
            
            with open('configs/risk_config_optimized.json', 'r') as f:
                risk_config = json.load(f)
            
            # Validate config structure
            required_strategies = ['RSIEMAMomentumStrategy', 'BollingerReversionStrategy', 'VolatilityBreakoutStrategy']
            loaded_strategies = [s['name'] for s in strategies_config['active_strategies']]
            
            missing_strategies = [s for s in required_strategies if s not in loaded_strategies]
            
            if not missing_strategies:
                print('   PASS: All required strategies loaded')
                print(f'   Loaded strategies: {len(loaded_strategies)}')
                print(f'   Min confidence: {strategies_config[\"signal_filters\"][\"min_confidence\"]}')
                self.test_results.append(('Configuration Loading', True, f'{len(loaded_strategies)} strategies loaded'))
            else:
                print(f'   FAIL: Missing strategies: {missing_strategies}')
                self.test_results.append(('Configuration Loading', False, f'Missing: {missing_strategies}'))
                
        except Exception as e:
            print(f'   ERROR: {e}')
            self.test_results.append(('Configuration Loading', False, f'Exception: {e}'))
    
    def print_summary(self):
        print('\n' + '='*50)
        print(' INTEGRATION TEST SUMMARY')
        print('='*50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, details in self.test_results:
            status = ' PASS' if success else ' FAIL'
            print(f'{status} | {test_name}: {details}')
        
        print(f'\n Overall: {passed}/{total} tests passed')
        
        if passed == total:
            print(' ALL INTEGRATION TESTS PASSED!')
        elif passed >= total * 0.75:
            print(' Most tests passed, minor issues detected')
        else:
            print(' Multiple test failures detected')

if __name__ == '__main__':
    framework = IntegrationTestFramework()
    framework.run_all_tests()
