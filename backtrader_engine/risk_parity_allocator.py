#!/usr/bin/env python3
"""
Risk Parity Allocator

Implementa asignación de capital basada en riesgo (Risk Parity) para estrategias de trading.
Dos métodos principales:
1. Risk Parity por Drawdown: peso ∝ 1 / max_drawdown
2. Risk Parity por Volatilidad: peso ∝ 1 / σ(returns)

Incluye clipping de pesos, umbral de rebalance y fricciones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


@dataclass
class AllocationResult:
    """Resultado de la asignación de capital"""
    weights: Dict[str, float]
    risk_metrics: Dict[str, float]
    rebalanced: bool
    drift: float
    total_risk: float


class RiskParityAllocator:
    """
    Allocator de capital basado en Risk Parity
    
    Implementa dos métodos:
    - max_dd: Basado en máximo drawdown histórico
    - volatility: Basado en volatilidad de retornos
    """
    
    def __init__(self, 
                 lookback: int = 365,
                 method: str = "max_dd",
                 w_min: float = 0.05,
                 w_max: float = 0.40,
                 rebalance_threshold: float = 0.20,
                 min_trades: int = 10):
        """
        Inicializar Risk Parity Allocator
        
        Args:
            lookback: Ventana de lookback para cálculo de métricas (días)
            method: Método de cálculo ("max_dd" o "volatility")
            w_min: Peso mínimo por estrategia (5%)
            w_max: Peso máximo por estrategia (40%)
            rebalance_threshold: Umbral para rebalance (20% de cambio)
            min_trades: Número mínimo de trades para considerar estrategia
        """
        self.lookback = lookback
        self.method = method
        self.w_min = w_min
        self.w_max = w_max
        self.rebalance_threshold = rebalance_threshold
        self.min_trades = min_trades
        
        # Estado interno
        self.last_weights = None
        self.equity_curves = {}
        self.risk_metrics_history = {}
        
        print(f"[RISK PARITY] Initialized with method: {method}")
        print(f"[RISK PARITY] Lookback: {lookback} days, Weights: [{w_min:.1%}, {w_max:.1%}]")
        print(f"[RISK PARITY] Rebalance threshold: {rebalance_threshold:.1%}")

    def update_equity_curve(self, strategy_name: str, equity_curve: pd.Series) -> None:
        """
        Actualizar curva de equity para una estrategia
        
        Args:
            strategy_name: Nombre de la estrategia
            equity_curve: Serie temporal de equity (valor del portfolio)
        """
        if not isinstance(equity_curve, pd.Series):
            raise ValueError("equity_curve must be a pandas Series")
            
        if not isinstance(equity_curve.index, pd.DatetimeIndex):
            raise ValueError("equity_curve index must be DatetimeIndex")
            
        self.equity_curves[strategy_name] = equity_curve.sort_index()
        print(f"[RISK PARITY] Updated equity curve for {strategy_name}: {len(equity_curve)} points")

    def compute_risk_metric(self, strategy_name: str) -> float:
        """
        Calcular métrica de riesgo para una estrategia
        
        Args:
            strategy_name: Nombre de la estrategia
            
        Returns:
            Métrica de riesgo (drawdown o volatilidad)
        """
        if strategy_name not in self.equity_curves:
            print(f"⚠️  No equity curve for {strategy_name}")
            return 1e-6  # Valor mínimo para evitar división por cero
            
        equity = self.equity_curves[strategy_name]
        
        # Filtrar por lookback
        if len(equity) > self.lookback:
            equity_lb = equity.iloc[-self.lookback:]
        else:
            equity_lb = equity
            
        if len(equity_lb) < 10:  # Mínimo de datos
            return 1e-6
            
        if self.method == "max_dd":
            # Calcular máximo drawdown
            peak = equity_lb.cummax()
            drawdown = (equity_lb / peak - 1.0).min()  # Negativo
            risk_metric = abs(drawdown) if drawdown < 0 else 1e-6
            
        elif self.method == "volatility":
            # Calcular volatilidad de retornos
            returns = equity_lb.pct_change().dropna()
            if len(returns) < 5:
                return 1e-6
            risk_metric = returns.std() if returns.std() > 0 else 1e-6
            
        else:
            raise ValueError(f"Unknown method: {self.method}")
            
        # Almacenar historial
        if strategy_name not in self.risk_metrics_history:
            self.risk_metrics_history[strategy_name] = []
        self.risk_metrics_history[strategy_name].append({
            'timestamp': equity_lb.index[-1],
            'risk_metric': risk_metric,
            'method': self.method
        })
        
        return risk_metric

    def compute_weights(self, strategy_names: List[str]) -> AllocationResult:
        """
        Calcular pesos de Risk Parity para las estrategias
        
        Args:
            strategy_names: Lista de nombres de estrategias
            
        Returns:
            AllocationResult con pesos y métricas
        """
        if not strategy_names:
            return AllocationResult(
                weights={},
                risk_metrics={},
                rebalanced=False,
                drift=0.0,
                total_risk=0.0
            )
        
        # Calcular métricas de riesgo
        risk_metrics = {}
        for strategy in strategy_names:
            risk_metrics[strategy] = self.compute_risk_metric(strategy)
        
        # Calcular pesos inversos (1/risk)
        inv_weights = {}
        for strategy, risk in risk_metrics.items():
            inv_weights[strategy] = 1.0 / max(risk, 1e-6)
        
        # Normalizar pesos
        total_inv = sum(inv_weights.values())
        raw_weights = {k: v / total_inv for k, v in inv_weights.items()}
        
        # Aplicar clipping
        clipped_weights = {}
        for strategy, weight in raw_weights.items():
            clipped_weights[strategy] = max(self.w_min, min(self.w_max, weight))
        
        # Renormalizar después del clipping
        total_clipped = sum(clipped_weights.values())
        if total_clipped > 0:
            final_weights = {k: v / total_clipped for k, v in clipped_weights.items()}
        else:
            # Fallback: pesos iguales
            final_weights = {k: 1.0 / len(strategy_names) for k in strategy_names}
        
        # Calcular drift desde última asignación
        drift = 0.0
        rebalanced = False
        
        if self.last_weights:
            drift = max(abs(final_weights.get(k, 0) - self.last_weights.get(k, 0)) 
                       for k in set(final_weights.keys()) | set(self.last_weights.keys()))
            
            if drift >= self.rebalance_threshold:
                rebalanced = True
                self.last_weights = final_weights.copy()
                print(f"[RISK PARITY] Rebalanced! Drift: {drift:.1%}")
            else:
                print(f"[RISK PARITY] No rebalance needed. Drift: {drift:.1%}")
        else:
            rebalanced = True
            self.last_weights = final_weights.copy()
            print(f"[RISK PARITY] Initial allocation")
        
        # Calcular riesgo total del portfolio
        total_risk = sum(final_weights[k] * risk_metrics[k] for k in final_weights)
        
        return AllocationResult(
            weights=final_weights,
            risk_metrics=risk_metrics,
            rebalanced=rebalanced,
            drift=drift,
            total_risk=total_risk
        )

    def get_allocation_summary(self, strategy_names: List[str]) -> Dict[str, Any]:
        """
        Obtener resumen de la asignación actual
        
        Args:
            strategy_names: Lista de nombres de estrategias
            
        Returns:
            Diccionario con resumen de asignación
        """
        result = self.compute_weights(strategy_names)
        
        summary = {
            'method': self.method,
            'lookback_days': self.lookback,
            'rebalance_threshold': self.rebalance_threshold,
            'weights': result.weights,
            'risk_metrics': result.risk_metrics,
            'rebalanced': result.rebalanced,
            'drift': result.drift,
            'total_risk': result.total_risk,
            'weight_constraints': {
                'min_weight': self.w_min,
                'max_weight': self.w_max
            }
        }
        
        return summary

    def print_allocation_summary(self, strategy_names: List[str]) -> None:
        """
        Imprimir resumen de asignación de capital
        
        Args:
            strategy_names: Lista de nombres de estrategias
        """
        result = self.compute_weights(strategy_names)
        
        print("\n" + "="*60)
        print("📊 RISK PARITY ALLOCATION SUMMARY")
        print("="*60)
        
        print(f"\n🎯 Method: {self.method.upper()}")
        print(f"📅 Lookback: {self.lookback} days")
        print(f"⚖️  Weight Range: [{self.w_min:.1%}, {self.w_max:.1%}]")
        print(f"🔄 Rebalance Threshold: {self.rebalance_threshold:.1%}")
        
        print(f"\n📈 Strategy Allocation:")
        for strategy, weight in result.weights.items():
            risk = result.risk_metrics.get(strategy, 0)
            print(f"  {strategy}: {weight:.1%} (Risk: {risk:.3f})")
        
        print(f"\n📊 Portfolio Metrics:")
        print(f"  Total Risk: {result.total_risk:.3f}")
        print(f"  Rebalanced: {'Yes' if result.rebalanced else 'No'}")
        print(f"  Drift: {result.drift:.1%}")
        
        # Mostrar métricas de riesgo
        print(f"\n🔍 Risk Metrics ({self.method}):")
        for strategy, risk in result.risk_metrics.items():
            print(f"  {strategy}: {risk:.4f}")

    def simulate_allocation(self, strategy_names: List[str], 
                          start_date: datetime, end_date: datetime,
                          rebalance_frequency: str = 'weekly') -> pd.DataFrame:
        """
        Simular asignación de capital a lo largo del tiempo
        
        Args:
            strategy_names: Lista de nombres de estrategias
            start_date: Fecha de inicio
            end_date: Fecha de fin
            rebalance_frequency: Frecuencia de rebalance ('daily', 'weekly', 'monthly')
            
        Returns:
            DataFrame con historial de asignaciones
        """
        # Generar fechas de rebalance
        if rebalance_frequency == 'daily':
            freq = 'D'
        elif rebalance_frequency == 'weekly':
            freq = 'W'
        elif rebalance_frequency == 'monthly':
            freq = 'M'
        else:
            raise ValueError(f"Unknown frequency: {rebalance_frequency}")
        
        rebalance_dates = pd.date_range(start_date, end_date, freq=freq)
        
        allocation_history = []
        
        for date in rebalance_dates:
            # Filtrar equity curves hasta esta fecha
            filtered_curves = {}
            for strategy in strategy_names:
                if strategy in self.equity_curves:
                    curve = self.equity_curves[strategy]
                    filtered_curve = curve[curve.index <= date]
                    if len(filtered_curve) > 0:
                        filtered_curves[strategy] = filtered_curve
            
            if not filtered_curves:
                continue
                
            # Calcular asignación
            result = self.compute_weights(list(filtered_curves.keys()))
            
            allocation_history.append({
                'date': date,
                'weights': result.weights.copy(),
                'risk_metrics': result.risk_metrics.copy(),
                'rebalanced': result.rebalanced,
                'drift': result.drift,
                'total_risk': result.total_risk
            })
        
        return pd.DataFrame(allocation_history)


def test_risk_parity_allocator():
    """Función de prueba para el Risk Parity Allocator"""
    print("🧪 Testing Risk Parity Allocator...")
    
    # Crear datos de prueba
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    
    # Simular 3 estrategias con diferentes perfiles de riesgo
    strategies = ['Strategy_A', 'Strategy_B', 'Strategy_C']
    
    # Strategy A: Baja volatilidad, bajo drawdown
    equity_a = 10000 * (1 + np.cumsum(np.random.normal(0.0005, 0.01, len(dates))))
    
    # Strategy B: Media volatilidad, drawdown moderado
    equity_b = 10000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
    
    # Strategy C: Alta volatilidad, alto drawdown
    equity_c = 10000 * (1 + np.cumsum(np.random.normal(0.002, 0.03, len(dates))))
    
    # Crear allocator
    allocator = RiskParityAllocator(method="max_dd", lookback=90)
    
    # Actualizar equity curves
    allocator.update_equity_curve('Strategy_A', pd.Series(equity_a, index=dates))
    allocator.update_equity_curve('Strategy_B', pd.Series(equity_b, index=dates))
    allocator.update_equity_curve('Strategy_C', pd.Series(equity_c, index=dates))
    
    # Calcular asignación
    allocator.print_allocation_summary(strategies)
    
    # Simular asignación a lo largo del tiempo
    print(f"\n📊 Simulating allocation over time...")
    history = allocator.simulate_allocation(
        strategies, 
        datetime(2024, 6, 1), 
        datetime(2024, 12, 31),
        'monthly'
    )
    
    print(f"📈 Allocation history: {len(history)} periods")
    print(history[['date', 'rebalanced', 'drift', 'total_risk']].tail())


if __name__ == "__main__":
    test_risk_parity_allocator()
