#!/usr/bin/env python3
"""
Market Regime Detector

Detecta regímenes de mercado basado en:
- Tendencia: precio vs EMA200 (bull/bear)
- Volatilidad: ATR(14)/close (alto/bajo basado en percentiles)
- Define 4 regímenes principales con whitelist de estrategias
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Regime:
    """Estructura para representar un régimen de mercado"""
    name: str
    trend: str  # "UP" or "DOWN"
    vol_bucket: str  # "HIGH", "MID", "LOW"
    strategy_whitelist: List[str]
    description: str = ""


class MarketRegimeDetector:
    """
    Detector de regímenes de mercado basado en tendencia y volatilidad
    
    Regímenes definidos:
    - BULL_TREND_LOW_VOL: Favorece TrendFollowing, EMA Breakout
    - BULL_TREND_HIGH_VOL: TF + ATR Breakout (recorta mean-reversion)
    - BEAR_TREND_HIGH_VOL: Contrarian/BB Reversion con sizing conservador
    - SIDEWAYS_LOW_VOL: Mean-reversion (BB/RSI-Vol), reduce breakout
    """
    
    def __init__(self, 
                 ema_period: int = 200,
                 atr_period: int = 14, 
                 lookback_vol: int = 180,
                 vol_high_percentile: float = 0.75,
                 vol_low_percentile: float = 0.25):
        """
        Inicializar el detector de regímenes
        
        Args:
            ema_period: Período para EMA de tendencia
            atr_period: Período para ATR
            lookback_vol: Ventana para cálculo de percentiles de volatilidad
            vol_high_percentile: Percentil para volatilidad alta
            vol_low_percentile: Percentil para volatilidad baja
        """
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.lookback_vol = lookback_vol
        self.vol_high_percentile = vol_high_percentile
        self.vol_low_percentile = vol_low_percentile
        
        # Definir whitelist de estrategias por régimen
        self.regime_strategies = {
            "BULL_TREND_LOW_VOL": [
                "TrendFollowingADXEMAStrategy",
                "EMABreakoutConservativeStrategy"
            ],
            "BULL_TREND_HIGH_VOL": [
                "TrendFollowingADXEMAStrategy", 
                "VolatilityBreakoutStrategy"
            ],
            "BEAR_TREND_HIGH_VOL": [
                "BollingerReversionStrategy",
                "ContrarianVolumeSpikeStrategy"
            ],
            "SIDEWAYS_LOW_VOL": [
                "BollingerReversionStrategy",
                "ContrarianVolumeSpikeStrategy"
            ]
        }
        
        # Datos procesados
        self.daily_df = None
        self.ema = None
        self.atr = None
        self.vol = None
        self.vol_q75 = None
        self.vol_q25 = None
        
        print(f"[REGIME DETECTOR] Initialized with EMA({ema_period}), ATR({atr_period}), Vol Lookback({lookback_vol})")
        print(f"[REGIME DETECTOR] Vol percentiles: High({vol_high_percentile}), Low({vol_low_percentile})")

    def prepare_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convertir datos de timeframe menor a diario
        
        Args:
            df: DataFrame con datos OHLCV (puede ser 15min, 1h, etc.)
            
        Returns:
            DataFrame con datos diarios
        """
        if df.empty:
            raise ValueError("DataFrame is empty")
            
        # Asegurar que el índice es datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
            
        # Resample a diario
        daily = df.resample('D').agg({
            'open': 'first',
            'high': 'max', 
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        print(f"[REGIME DETECTOR] Resampled {len(df)} bars to {len(daily)} daily bars")
        print(f"[REGIME DETECTOR] Daily range: {daily.index[0]} to {daily.index[-1]}")
        
        return daily

    def calculate_indicators(self, daily_df: pd.DataFrame) -> None:
        """
        Calcular indicadores técnicos para detección de regímenes
        
        Args:
            daily_df: DataFrame con datos diarios OHLCV
        """
        self.daily_df = daily_df.copy()
        
        # EMA para tendencia
        self.ema = self.daily_df['close'].ewm(span=self.ema_period, adjust=False).mean()
        
        # ATR para volatilidad
        high_low = self.daily_df['high'] - self.daily_df['low']
        high_close = np.abs(self.daily_df['high'] - self.daily_df['close'].shift())
        low_close = np.abs(self.daily_df['low'] - self.daily_df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.atr = true_range.rolling(window=self.atr_period).mean()
        
        # Volatilidad normalizada (ATR/close)
        self.vol = (self.atr / self.daily_df['close']).rolling(window=self.lookback_vol).mean()
        
        # Percentiles de volatilidad
        self.vol_q75 = self.vol.rolling(window=self.lookback_vol).quantile(self.vol_high_percentile)
        self.vol_q25 = self.vol.rolling(window=self.lookback_vol).quantile(self.vol_low_percentile)
        
        print(f"[REGIME DETECTOR] Indicators calculated for {len(self.daily_df)} daily bars")
        print(f"[REGIME DETECTOR] EMA period: {self.ema_period}, ATR period: {self.atr_period}")

    def regime_at(self, timestamp: datetime) -> Regime:
        """
        Determinar el régimen de mercado en un timestamp específico
        
        Args:
            timestamp: Timestamp para el cual determinar el régimen
            
        Returns:
            Objeto Regime con información del régimen detectado
        """
        if self.daily_df is None:
            raise ValueError("Must call calculate_indicators() first")
            
        # Encontrar el índice más cercano (pad method)
        try:
            idx = self.daily_df.index.get_indexer([timestamp], method='pad')[0]
            if idx == -1:
                # Si no hay datos anteriores, usar el primer índice disponible
                idx = 0
        except (KeyError, IndexError):
            # Si el timestamp no está en el índice, usar el más cercano
            idx = self.daily_df.index.get_indexer([timestamp], method='nearest')[0]
            if idx == -1:
                idx = 0
        
        # Obtener valores en el índice
        price = self.daily_df['close'].iloc[idx]
        ema_val = self.ema.iloc[idx]
        vol_val = self.vol.iloc[idx]
        vol_q75_val = self.vol_q75.iloc[idx]
        vol_q25_val = self.vol_q25.iloc[idx]
        
        # Determinar tendencia
        trend = "UP" if price > ema_val else "DOWN"
        
        # Determinar bucket de volatilidad
        if pd.isna(vol_val) or pd.isna(vol_q75_val) or pd.isna(vol_q25_val):
            vol_bucket = "MID"  # Default si no hay datos suficientes
        elif vol_val > vol_q75_val:
            vol_bucket = "HIGH"
        elif vol_val < vol_q25_val:
            vol_bucket = "LOW"
        else:
            vol_bucket = "MID"
        
        # Determinar régimen
        if trend == "UP" and vol_bucket == "LOW":
            regime_name = "BULL_TREND_LOW_VOL"
            description = "Tendencia alcista con baja volatilidad - Ideal para trend following"
        elif trend == "UP" and vol_bucket == "HIGH":
            regime_name = "BULL_TREND_HIGH_VOL"
            description = "Tendencia alcista con alta volatilidad - Favorece breakouts"
        elif trend == "DOWN" and vol_bucket == "HIGH":
            regime_name = "BEAR_TREND_HIGH_VOL"
            description = "Tendencia bajista con alta volatilidad - Contrarian strategies"
        else:
            regime_name = "SIDEWAYS_LOW_VOL"
            description = "Mercado lateral con baja volatilidad - Mean reversion"
        
        # Obtener whitelist de estrategias
        strategy_whitelist = self.regime_strategies.get(regime_name, [])
        
        return Regime(
            name=regime_name,
            trend=trend,
            vol_bucket=vol_bucket,
            strategy_whitelist=strategy_whitelist,
            description=description
        )

    def get_regime_history(self, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Obtener historial de regímenes para un período
        
        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            
        Returns:
            DataFrame con historial de regímenes
        """
        if self.daily_df is None:
            raise ValueError("Must call calculate_indicators() first")
            
        # Filtrar fechas si se especifican
        df_filtered = self.daily_df.copy()
        if start_date:
            df_filtered = df_filtered[df_filtered.index >= start_date]
        if end_date:
            df_filtered = df_filtered[df_filtered.index <= end_date]
        
        # Calcular regímenes para cada fecha
        regimes = []
        for timestamp in df_filtered.index:
            regime = self.regime_at(timestamp)
            regimes.append({
                'date': timestamp,
                'regime': regime.name,
                'trend': regime.trend,
                'vol_bucket': regime.vol_bucket,
                'price': df_filtered.loc[timestamp, 'close'],
                'ema': self.ema.loc[timestamp],
                'vol': self.vol.loc[timestamp],
                'vol_q75': self.vol_q75.loc[timestamp],
                'vol_q25': self.vol_q25.loc[timestamp],
                'strategies': ', '.join(regime.strategy_whitelist)
            })
        
        return pd.DataFrame(regimes)

    def get_current_regime(self) -> Regime:
        """
        Obtener el régimen actual (última fecha disponible)
        
        Returns:
            Objeto Regime actual
        """
        if self.daily_df is None:
            raise ValueError("Must call calculate_indicators() first")
            
        last_timestamp = self.daily_df.index[-1]
        return self.regime_at(last_timestamp)

    def print_regime_summary(self) -> None:
        """Imprimir resumen de regímenes detectados"""
        if self.daily_df is None:
            print("[REGIME DETECTOR] No data available")
            return
            
        history = self.get_regime_history()
        
        print("\n" + "="*60)
        print("📊 MARKET REGIME DETECTOR SUMMARY")
        print("="*60)
        
        # Estadísticas por régimen
        regime_counts = history['regime'].value_counts()
        print(f"\n📈 Regime Distribution:")
        for regime, count in regime_counts.items():
            percentage = (count / len(history)) * 100
            print(f"  {regime}: {count} days ({percentage:.1f}%)")
        
        # Régimen actual
        current = self.get_current_regime()
        print(f"\n🎯 Current Regime: {current.name}")
        print(f"   Trend: {current.trend}")
        print(f"   Volatility: {current.vol_bucket}")
        print(f"   Active Strategies: {', '.join(current.strategy_whitelist)}")
        print(f"   Description: {current.description}")
        
        # Últimos valores
        last_row = history.iloc[-1]
        print(f"\n📊 Latest Values:")
        print(f"   Price: ${last_row['price']:,.2f}")
        print(f"   EMA{self.ema_period}: ${last_row['ema']:,.2f}")
        print(f"   Volatility: {last_row['vol']:.4f}")
        print(f"   Vol Q75: {last_row['vol_q75']:.4f}")
        print(f"   Vol Q25: {last_row['vol_q25']:.4f}")


def test_regime_detector():
    """Función de prueba para el detector de regímenes"""
    print("🧪 Testing Market Regime Detector...")
    
    # Crear datos de prueba
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    np.random.seed(42)
    
    # Simular precio con tendencia y volatilidad variable
    price = 50000
    prices = []
    for i in range(len(dates)):
        # Tendencia alcista con volatilidad variable
        trend = 0.001 if i < len(dates)//2 else -0.0005
        vol = 0.02 if i % 30 < 15 else 0.05  # Volatilidad alternante
        
        price += price * (trend + np.random.normal(0, vol))
        prices.append(price)
    
    test_df = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 10000) for _ in prices]
    }, index=dates)
    
    # Probar detector
    detector = MarketRegimeDetector()
    detector.calculate_indicators(test_df)
    detector.print_regime_summary()
    
    # Probar régimen específico
    test_date = datetime(2024, 6, 15)
    regime = detector.regime_at(test_date)
    print(f"\n🔍 Test regime at {test_date}: {regime.name}")


if __name__ == "__main__":
    test_regime_detector()
