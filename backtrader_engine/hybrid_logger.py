#!/usr/bin/env python3
"""
Hybrid Logging System

Sistema de logging híbrido para el portfolio engine que incluye:
- Logging incremental por timestamp
- Formato JSON Lines (.jsonl) para análisis
- Logging híbrido JSON + TXT
- Auto-nombrado de sesiones
- Integración completa con todos los componentes
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import threading


class HybridLogger:
    """
    Sistema de logging híbrido para portfolio engine
    
    Características:
    - Logging incremental por timestamp
    - Formato JSON Lines (.jsonl)
    - Logging híbrido JSON + TXT
    - Auto-nombrado de sesiones
    - Thread-safe
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Inicializar HybridLogger
        
        Args:
            session_id: ID de sesión personalizado (opcional)
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = Path(__file__).parent / 'reports' / f'portfolio_{self.session_id}'
        self.strategies_dir = self.session_dir / 'strategies'
        
        # Crear directorios
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.strategies_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread lock para operaciones concurrentes
        self._lock = threading.Lock()
        
        # Configurar loggers
        self._setup_loggers()
        
        # Archivos de log
        self._log_files = {
            'execution': self.session_dir / 'execution_log.txt',
            'regime_detection': self.session_dir / 'regime_detection.jsonl',
            'risk_parity': self.session_dir / 'risk_parity.jsonl',
            'strategy_handles': self.session_dir / 'strategy_handles.jsonl',
            'portfolio_summary': self.session_dir / 'portfolio_summary.json'
        }
        
        # Inicializar archivos
        self._initialize_log_files()
        
        print(f"📁 Hybrid Logger initialized: {self.session_dir}")

    def _setup_loggers(self):
        """Configurar loggers para diferentes componentes"""
        
        # Logger principal de ejecución
        self.execution_logger = logging.getLogger(f'execution_{self.session_id}')
        self.execution_logger.setLevel(logging.INFO)
        
        # Handler para archivo de ejecución
        execution_handler = logging.FileHandler(
            self.session_dir / 'execution_log.txt',
            mode='w',
            encoding='utf-8'
        )
        execution_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        execution_handler.setFormatter(execution_formatter)
        self.execution_logger.addHandler(execution_handler)
        
        # Logger para consola
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.execution_logger.addHandler(console_handler)

    def _initialize_log_files(self):
        """Inicializar archivos de log"""
        with self._lock:
            # Crear archivos JSONL vacíos
            for log_type in ['regime_detection', 'risk_parity', 'strategy_handles']:
                with open(self._log_files[log_type], 'w', encoding='utf-8') as f:
                    pass  # Archivo vacío
            
            # Crear archivo de resumen de portfolio
            with open(self._log_files['portfolio_summary'], 'w', encoding='utf-8') as f:
                json.dump({
                    'session_id': self.session_id,
                    'start_time': datetime.now().isoformat(),
                    'status': 'initialized'
                }, f, indent=2)

    def log_execution(self, level: str, message: str, **kwargs):
        """
        Log de ejecución general
        
        Args:
            level: Nivel de log (INFO, WARNING, ERROR, DEBUG)
            message: Mensaje de log
            **kwargs: Datos adicionales
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if kwargs:
            message += f" | Data: {kwargs}"
        
        self.execution_logger.log(log_level, message)

    def log_regime_detection(self, data: Dict[str, Any]):
        """
        Log de detección de régimen
        
        Args:
            data: Datos del régimen detectado
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'regime_detection',
            'data': data
        }
        
        with self._lock:
            with open(self._log_files['regime_detection'], 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

    def log_risk_parity(self, data: Dict[str, Any]):
        """
        Log de Risk Parity
        
        Args:
            data: Datos de Risk Parity (pesos, rebalances, etc.)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'risk_parity',
            'data': data
        }
        
        with self._lock:
            with open(self._log_files['risk_parity'], 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

    def log_strategy_handle(self, strategy_name: str, action: str, data: Dict[str, Any]):
        """
        Log de StrategyHandle
        
        Args:
            strategy_name: Nombre de la estrategia
            action: Acción realizada (ENABLED, DISABLED, SYNC, etc.)
            data: Datos de la acción
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'strategy_handle',
            'strategy_name': strategy_name,
            'action': action,
            'data': data
        }
        
        with self._lock:
            with open(self._log_files['strategy_handles'], 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

    def save_strategy_result(self, strategy_name: str, result: Dict[str, Any]):
        """
        Guardar resultado individual de estrategia
        
        Args:
            strategy_name: Nombre de la estrategia
            result: Resultado de la estrategia
        """
        strategy_file = self.strategies_dir / f'{strategy_name}.json'
        
        with self._lock:
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str)

    def update_portfolio_summary(self, summary: Dict[str, Any]):
        """
        Actualizar resumen del portfolio
        
        Args:
            summary: Resumen del portfolio
        """
        summary['last_update'] = datetime.now().isoformat()
        
        with self._lock:
            with open(self._log_files['portfolio_summary'], 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)

    def finalize_session(self, final_summary: Dict[str, Any]):
        """
        Finalizar sesión de logging
        
        Args:
            final_summary: Resumen final de la sesión
        """
        final_summary['end_time'] = datetime.now().isoformat()
        final_summary['status'] = 'completed'
        
        self.update_portfolio_summary(final_summary)
        
        # Log final
        self.log_execution('INFO', f"Session {self.session_id} completed successfully")
        
        print(f"✅ Session {self.session_id} finalized: {self.session_dir}")

    def get_session_info(self) -> Dict[str, Any]:
        """Obtener información de la sesión"""
        return {
            'session_id': self.session_id,
            'session_dir': str(self.session_dir),
            'log_files': {k: str(v) for k, v in self._log_files.items()}
        }

    def read_log_file(self, log_type: str) -> List[Dict[str, Any]]:
        """
        Leer archivo de log JSONL
        
        Args:
            log_type: Tipo de log (regime_detection, risk_parity, strategy_handles)
            
        Returns:
            Lista de entradas de log
        """
        if log_type not in self._log_files:
            raise ValueError(f"Unknown log type: {log_type}")
        
        entries = []
        with open(self._log_files[log_type], 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        return entries

    def get_strategy_results(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todos los resultados de estrategias"""
        results = {}
        
        for strategy_file in self.strategies_dir.glob('*.json'):
            strategy_name = strategy_file.stem
            with open(strategy_file, 'r', encoding='utf-8') as f:
                results[strategy_name] = json.load(f)
        
        return results


class StrategyHandleLogger:
    """
    Logger específico para StrategyHandle
    
    Integra hooks de logging en StrategyHandle
    """
    
    def __init__(self, hybrid_logger: HybridLogger, strategy_name: str):
        self.hybrid_logger = hybrid_logger
        self.strategy_name = strategy_name
    
    def log_enable(self, timestamp: datetime, equity: float, **kwargs):
        """Log cuando se habilita una estrategia"""
        data = {
            'equity': equity,
            'action': 'ENABLED',
            **kwargs
        }
        self.hybrid_logger.log_strategy_handle(self.strategy_name, 'ENABLED', data)
    
    def log_disable(self, timestamp: datetime, equity: float, **kwargs):
        """Log cuando se deshabilita una estrategia"""
        data = {
            'equity': equity,
            'action': 'DISABLED',
            **kwargs
        }
        self.hybrid_logger.log_strategy_handle(self.strategy_name, 'DISABLED', data)
    
    def log_sync(self, timestamp: datetime, target_value: float, current_value: float, delta: float, **kwargs):
        """Log cuando se sincroniza una estrategia"""
        data = {
            'target_value': target_value,
            'current_value': current_value,
            'delta': delta,
            'action': 'SYNC',
            **kwargs
        }
        self.hybrid_logger.log_strategy_handle(self.strategy_name, 'SYNC', data)
    
    def log_trade(self, timestamp: datetime, trade_type: str, price: float, size: float, **kwargs):
        """Log de trades"""
        data = {
            'trade_type': trade_type,
            'price': price,
            'size': size,
            'action': 'TRADE',
            **kwargs
        }
        self.hybrid_logger.log_strategy_handle(self.strategy_name, 'TRADE', data)


class RiskParityLogger:
    """
    Logger específico para Risk Parity
    """
    
    def __init__(self, hybrid_logger: HybridLogger):
        self.hybrid_logger = hybrid_logger
    
    def log_rebalance(self, weights: Dict[str, float], drift: float, rebalanced: bool, **kwargs):
        """Log de rebalance de Risk Parity"""
        data = {
            'weights': weights,
            'drift': drift,
            'rebalanced': rebalanced,
            'action': 'REBALANCE',
            **kwargs
        }
        self.hybrid_logger.log_risk_parity(data)
    
    def log_allocation(self, strategy_names: List[str], allocation_result: Any, **kwargs):
        """Log de asignación de Risk Parity"""
        data = {
            'strategy_names': strategy_names,
            'allocation_result': allocation_result.__dict__ if hasattr(allocation_result, '__dict__') else str(allocation_result),
            'action': 'ALLOCATION',
            **kwargs
        }
        self.hybrid_logger.log_risk_parity(data)


class RegimeDetectionLogger:
    """
    Logger específico para Market Regime Detection
    """
    
    def __init__(self, hybrid_logger: HybridLogger):
        self.hybrid_logger = hybrid_logger
    
    def log_regime_change(self, old_regime: str, new_regime: str, timestamp: datetime, **kwargs):
        """Log de cambio de régimen"""
        data = {
            'old_regime': old_regime,
            'new_regime': new_regime,
            'timestamp': timestamp.isoformat(),
            'action': 'REGIME_CHANGE',
            **kwargs
        }
        self.hybrid_logger.log_regime_detection(data)
    
    def log_regime_analysis(self, regime: str, trend: str, volatility: str, active_strategies: List[str], **kwargs):
        """Log de análisis de régimen"""
        data = {
            'regime': regime,
            'trend': trend,
            'volatility': volatility,
            'active_strategies': active_strategies,
            'action': 'REGIME_ANALYSIS',
            **kwargs
        }
        self.hybrid_logger.log_regime_detection(data)


def test_hybrid_logger():
    """Función de prueba para HybridLogger"""
    print("🧪 Testing Hybrid Logger...")
    
    # Crear logger
    logger = HybridLogger()
    
    # Probar diferentes tipos de log
    logger.log_execution('INFO', 'Test execution log', test_data={'value': 123})
    
    logger.log_regime_detection({
        'regime': 'BULL_TREND_LOW_VOL',
        'trend': 'UP',
        'volatility': 'LOW',
        'active_strategies': ['EMABreakoutStrategy']
    })
    
    logger.log_risk_parity({
        'weights': {'Strategy_A': 0.4, 'Strategy_B': 0.6},
        'drift': 0.15,
        'rebalanced': True
    })
    
    logger.log_strategy_handle('TestStrategy', 'ENABLED', {
        'equity': 10000,
        'target_value': 10000
    })
    
    # Guardar resultado de estrategia
    logger.save_strategy_result('TestStrategy', {
        'performance': {'total_return': 5.2},
        'analyzers': {'sharpe': {'sharperatio': 1.5}}
    })
    
    # Actualizar resumen
    logger.update_portfolio_summary({
        'total_return': 5.2,
        'strategies_count': 1,
        'session_status': 'testing'
    })
    
    # Finalizar sesión
    logger.finalize_session({
        'total_return': 5.2,
        'strategies_count': 1,
        'final_status': 'completed'
    })
    
    print("✅ Hybrid Logger test completed")
    print(f"📁 Session directory: {logger.session_dir}")


if __name__ == "__main__":
    test_hybrid_logger()
