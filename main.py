"""
Main trading bot orchestrator.
"""

import time
import logging
import signal
import sys
import subprocess
import psutil
import os
from datetime import datetime
from typing import Optional

from config import Config
from data.data_fetcher import DataFetcher
from processing.kalman_filter import KalmanFilter
from processing.ml_model import MLModel
from strategy.liquidation_hunter import LiquidationHunter
from execution.trader import Trader
from monitoring.logger import BotLogger


class TradingBot:
    """Main trading bot orchestrator."""
    
    def __init__(self):
        """Initialize the trading bot."""
        self.config = Config()
        self.logger = BotLogger()
        self.data_fetcher = DataFetcher()
        self.kalman_filter = KalmanFilter()
        self.ml_model = MLModel()
        self.strategy = LiquidationHunter()
        self.trader = Trader()
        self.running = False
        self.dashboard_process = None
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _is_dashboard_running(self) -> bool:
        """Check if Streamlit dashboard is running on port 8501."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('streamlit' in arg for arg in cmdline):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            self.log.warning(f"Error checking dashboard status: {e}")
            return False
    
    def _start_dashboard(self):
        """Start the Streamlit dashboard."""
        try:
            if self._is_dashboard_running():
                self.log.info("Dashboard already running")
                return True
            
            self.log.info("Starting Streamlit dashboard...")
            
            # Command to start dashboard
            cmd = [
                "venv\\Scripts\\python.exe",
                "-m", "streamlit", "run", "dashboard_fixed.py"
            ]
            
            # Start dashboard process
            self.dashboard_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait a moment for dashboard to start
            time.sleep(3)
            
            # Verify it's running
            if self._is_dashboard_running():
                self.log.info("Dashboard started successfully at http://localhost:8501")
                return True
            else:
                self.log.warning("Dashboard may not have started properly")
                return False
                
        except Exception as e:
            self.log.error(f"Error starting dashboard: {e}")
            return False
    
    def _setup_logging(self):
        """Setup logging configuration."""
        import os
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/bot.log'),
                logging.StreamHandler()
            ]
        )
        self.log = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.log.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Stop dashboard if running
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.log.info("Dashboard stopped")
            except Exception as e:
                self.log.warning(f"Error stopping dashboard: {e}")
    
    def validate_components(self) -> bool:
        """Validate all bot components."""
        components = [
            self.config,
            self.data_fetcher,
            self.kalman_filter,
            self.ml_model,
            self.strategy,
            self.trader
        ]
        
        for component in components:
            if not hasattr(component, 'validate') or not component.validate():
                self.log.error(f"Component {component.__class__.__name__} validation failed")
                return False
        
        return True
    
    def run(self):
        """Main trading loop."""
        self.log.info("Starting trading bot...")
        self.log.info(f"Trading mode: {self.config.MODE.upper()}")
        
        # Start dashboard automatically
        self._start_dashboard()
        
        if not self.validate_components():
            self.log.error("Configuration or component validation failed. Exiting.")
            return
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                cycle_start = datetime.now()
                
                self.log.info(f"Starting trading cycle #{cycle_count} at {cycle_start}")
                
                try:
                    self._execute_trading_cycle()
                except Exception as e:
                    self.log.error(f"Error in trading cycle #{cycle_count}: {e}")
                    continue
                
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(0, self.config.UPDATE_INTERVAL - cycle_duration)
                
                self.log.info(f"Cycle #{cycle_count} completed in {cycle_duration:.2f} seconds. Waiting {sleep_time:.2f} seconds...")
                
                self._sleep_with_interrupt(sleep_time)
                
        except Exception as e:
            self.log.error(f"Unexpected error in main loop: {e}")
            raise
        finally:
            self.log.info("Bot shutdown complete")
    
    def _execute_trading_cycle(self):
        """Execute a single trading cycle with robust validation."""
        # 1. Validación robusta de datos
        data = self.data_fetcher.fetch_data()
        if not self._validate_data_quality(data):
            self.log.warning("Data quality validation failed, skipping cycle")
            return

        # 2. Aplicar filtro Kalman con validación
        filtered_data = self.kalman_filter.apply_filter(data)
        if not self._validate_filtered_data(filtered_data):
            self.log.warning("Kalman filter processing failed, skipping cycle")
            return

        # 3. Validar datos antes de predicción ML
        if not self._validate_ml_input_data(filtered_data):
            self.log.warning("ML input data validation failed, skipping cycle")
            return

        # 4. Hacer predicción con manejo de errores
        try:
            prediction = self.ml_model.predict(filtered_data)
            if prediction is None:
                self.log.warning("ML prediction returned None, skipping cycle")
                return
        except Exception as e:
            self.log.error(f"ML prediction error: {e}, skipping cycle")
            return

        # 5. Generar señal con validación
        try:
            signal = self.strategy.generate_signal(filtered_data, prediction)
            if signal:
                self.log.info(f"Generated signal: {signal}")
                result = self.trader.execute_trade(signal)
                if result:
                    self.log.info(f"Trade executed successfully: {result}")
                    self.logger.log_trade(result)
                else:
                    self.log.error("Trade execution failed")
            else:
                self.log.info("No trading signal generated")
        except Exception as e:
            self.log.error(f"Signal generation error: {e}")

    def _validate_data_quality(self, data) -> bool:
        """Validar calidad de datos de entrada"""
        if data is None:
            self.log.error("Data is None")
            return False
        
        if data.empty:
            self.log.error("Data is empty")
            return False
        
        # Verificar columnas requeridas
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            self.log.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Verificar valores nulos
        null_counts = data[required_columns].isnull().sum()
        if null_counts.any():
            self.log.error(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
            return False
        
        # Verificar valores negativos en precios
        price_columns = ['open', 'high', 'low', 'close']
        negative_prices = (data[price_columns] <= 0).any().any()
        if negative_prices:
            self.log.error("Negative or zero prices found")
            return False
        
        # Verificar valores negativos en volumen
        if (data['volume'] < 0).any():
            self.log.error("Negative volume found")
            return False
        
        # Verificar datos suficientes
        if len(data) < 10:
            self.log.warning(f"Insufficient data points: {len(data)}")
            return False
        
        return True

    def _validate_filtered_data(self, filtered_data) -> bool:
        """Validar datos filtrados por Kalman"""
        if filtered_data is None:
            self.log.error("Filtered data is None")
            return False
        
        if filtered_data.empty:
            self.log.error("Filtered data is empty")
            return False
        
        # Verificar columnas de Kalman
        kalman_columns = ['kalman_price', 'kalman_deviation', 'kalman_signal']
        missing_kalman = [col for col in kalman_columns if col not in filtered_data.columns]
        if missing_kalman:
            self.log.error(f"Missing Kalman columns: {missing_kalman}")
            return False
        
        # Verificar valores infinitos
        if filtered_data.isin([float('inf'), float('-inf')]).any().any():
            self.log.error("Infinite values found in filtered data")
            return False
        
        return True

    def _validate_ml_input_data(self, data) -> bool:
        """Validar datos de entrada para ML"""
        try:
            # Verificar que tenemos datos suficientes para ML
            if len(data) < 20:
                self.log.warning(f"Insufficient data for ML: {len(data)} points")
                return False
            
            # Verificar columnas necesarias para características ML
            ml_columns = ['sma_20', 'sma_50', 'price_change', 'volume_ratio', 'volatility']
            missing_ml = [col for col in ml_columns if col not in data.columns]
            if missing_ml:
                self.log.warning(f"Missing ML columns: {missing_ml}")
                return False
            
            # Verificar que tenemos suficientes datos válidos (sin NaN) en columnas críticas
            critical_columns = ['close', 'sma_20', 'sma_50', 'price_change']
            clean_data = data[critical_columns].dropna()
            
            if len(clean_data) < 20:
                self.log.warning(f"Insufficient clean data for ML: {len(clean_data)} points (need at least 20)")
                return False
            
            # Verificar que tenemos datos recientes válidos (últimos 50 puntos)
            recent_data = data[critical_columns].tail(50).dropna()
            if len(recent_data) < 10:
                self.log.warning(f"Insufficient recent clean data: {len(recent_data)} points")
                return False
            
            return True
        except Exception as e:
            self.log.error(f"ML input validation error: {e}")
            return False
    
    def _sleep_with_interrupt(self, sleep_time: float):
        """Sleep in small chunks to allow for graceful shutdown."""
        chunk_size = 1.0  # Sleep in 1-second chunks
        remaining_time = sleep_time
        
        while remaining_time > 0 and self.running:
            sleep_chunk = min(chunk_size, remaining_time)
            time.sleep(sleep_chunk)
            remaining_time -= sleep_chunk


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
