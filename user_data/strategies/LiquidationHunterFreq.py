"""
Liquidation Hunter Strategy for Freqtrade
Adapted from LiquidationHunterAICoded for QuantConnect
Uses strategy_parameters from config for simplicity and scalability
"""

import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import Optional, Dict, Any, Union
from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta
from freqtrade.persistence import Trade


class LiquidationHunterFreq(IStrategy):
    """
    Liquidation Hunter Strategy for Freqtrade

    This strategy combines:
    - Kalman Filter signals for trend detection
    - ML-like predictions using RSI and EMA crossovers
    - Risk management with stop loss and take profit
    
    Parameters are loaded from strategy_parameters in config file for simplicity.
    """

    INTERFACE_VERSION = 3

    # Strategy default (overridden by config) - NO DEFAULT VALUES
    # These will be taken from config file
    minimal_roi = None
    stoploss = None

    trailing_stop = False
    trailing_stop_positive = None
    trailing_stop_positive_offset = 0.0
    trailing_only_offset_is_reached = False

    timeframe = '1h'  # Will be overridden by config
    process_only_new_candles = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 30

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        
        # Load strategy parameters from config
        strategy_params = config.get("strategy_parameters", {})
        
        # Kalman Filter parameters
        self.kalman_threshold = strategy_params.get("kalman_threshold", 0.3)
        self.deviation_threshold = strategy_params.get("deviation_threshold", 1.5)
        self.ml_confidence_threshold = strategy_params.get("ml_confidence_threshold", 0.55)
        
        # Technical indicator parameters
        self.rsi_period = strategy_params.get("rsi_period", 14)
        self.ema_fast_period = strategy_params.get("ema_fast_period", 8)
        self.ema_slow_period = strategy_params.get("ema_slow_period", 21)
        
        # Logs para confirmar estrategia cargada correctamente
        print(f"[STRATEGY LOADED] {self.__class__.__name__}")
        print(f"[STRATEGY CONFIG] stoploss from config: {config.get('stoploss', 'NOT FOUND')}")
        print(f"[STRATEGY CONFIG] minimal_roi from config: {config.get('minimal_roi', 'NOT FOUND')}")
        print(f"[STRATEGY VALUES] self.stoploss: {self.stoploss}")
        print(f"[STRATEGY VALUES] self.minimal_roi: {self.minimal_roi}")
        print(f"[STRATEGY PARAMETERS] kalman_threshold: {self.kalman_threshold}")
        print(f"[STRATEGY PARAMETERS] deviation_threshold: {self.deviation_threshold}")
        print(f"[STRATEGY PARAMETERS] ml_confidence_threshold: {self.ml_confidence_threshold}")
        print(f"[STRATEGY PARAMETERS] rsi_period: {self.rsi_period}")
        print(f"[STRATEGY PARAMETERS] ema_fast_period: {self.ema_fast_period}")
        print(f"[STRATEGY PARAMETERS] ema_slow_period: {self.ema_slow_period}")

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Populate indicators for the strategy
        """
        # Technical indicators
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=self.ema_fast_period)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=self.ema_slow_period)

        # Kalman-like signals
        dataframe['kalman_signal'] = dataframe['close'] - dataframe['ema_fast']
        dataframe['kalman_deviation'] = dataframe['close'].rolling(window=9).std().fillna(0.0)

        # ML-like prediction signals
        dataframe['ml_prediction'] = 0
        dataframe['ml_confidence'] = 0.0

        # Long conditions (relaxed RSI thresholds)
        long_condition = (
            (dataframe['rsi'] < 40) |  # Relaxed from 30
            (dataframe['ema_fast'] > dataframe['ema_slow'])
        )

        # Short conditions (relaxed RSI thresholds)
        short_condition = (
            (dataframe['rsi'] > 60) |  # Relaxed from 70
            (dataframe['ema_fast'] < dataframe['ema_slow'])
        )

        # Set ML predictions
        dataframe.loc[long_condition, 'ml_prediction'] = 1
        dataframe.loc[short_condition, 'ml_prediction'] = 0

        # Set ML confidence based on RSI levels
        dataframe.loc[dataframe['rsi'] < 40, 'ml_confidence'] = 0.8
        dataframe.loc[dataframe['rsi'] > 60, 'ml_confidence'] = 0.8
        dataframe.loc[(dataframe['rsi'] >= 40) & (dataframe['rsi'] <= 60), 'ml_confidence'] = 0.6

        # Strategy conditions
        dataframe['strong_kalman'] = abs(dataframe['kalman_signal']) > self.kalman_threshold
        dataframe['high_deviation'] = dataframe['kalman_deviation'] > self.deviation_threshold
        dataframe['high_confidence'] = dataframe['ml_confidence'] > self.ml_confidence_threshold

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Populate entry signals
        """
        # Long entry conditions
        dataframe.loc[
            (
                dataframe['strong_kalman'] &
                dataframe['high_deviation'] &
                dataframe['high_confidence'] &
                (dataframe['ml_prediction'] == 1) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        # Short entry conditions
        dataframe.loc[
            (
                dataframe['strong_kalman'] &
                dataframe['high_deviation'] &
                (dataframe['ml_prediction'] == 0) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Populate exit signals
        """
        # Long exit conditions
        dataframe.loc[
            (
                (dataframe['rsi'] > 70) |
                (dataframe['ema_fast'] < dataframe['ema_slow'])
            ),
            'exit_long'] = 1

        # Short exit conditions
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) |
                (dataframe['ema_fast'] > dataframe['ema_slow'])
            ),
            'exit_short'] = 1

        return dataframe

    # custom_exit() intentionally removed to allow default stoploss and ROI to function