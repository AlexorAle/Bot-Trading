"""
Machine Learning model for price direction prediction.
Uses Random Forest for classification.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from typing import Tuple, Optional, Dict, Any
import logging
from config import Config


class MLModel:
    """Random Forest model for price direction prediction."""
    
    def __init__(self):
        """Initialize the ML model."""
        self.config = Config()
        self.log = logging.getLogger(__name__)
        self.model = None
        self.feature_columns = []
        self.model_path = 'models/rf_model.pkl'
        
        # Load existing model if available
        self._load_model()
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML model."""
        df = data.copy()
        
        # Price-based features
        df['price_change_1'] = df['close'].pct_change(1)
        df['price_change_5'] = df['close'].pct_change(5)
        df['price_change_10'] = df['close'].pct_change(10)
        
        # Technical indicators
        df['rsi'] = self._calculate_rsi(df['close'])
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change()
        df['volume_price_trend'] = df['volume'] * df['price_change_1']
        
        # Kalman filter features
        if 'kalman_deviation' in df.columns:
            df['kalman_signal_strength'] = abs(df['kalman_deviation'])
            df['kalman_trend'] = df['kalman_price'].diff()
        
        # Liquidation features
        if 'liquidations_volume' in df.columns:
            df['liquidation_ratio'] = df['liquidations_short'] / (df['liquidations_long'] + 1)
            df['liquidation_volume_ratio'] = df['liquidations_volume'] / (df['volume'] + 1)
            
            # Replace infinite values with 0
            df['liquidation_ratio'] = df['liquidation_ratio'].replace([np.inf, -np.inf], 0)
            df['liquidation_volume_ratio'] = df['liquidation_volume_ratio'].replace([np.inf, -np.inf], 0)
        
        # Remove NaN values and infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        return df
    
    def create_target(self, data: pd.DataFrame, lookahead: int = 5) -> pd.Series:
        """Create target variable for classification."""
        future_prices = data['close'].shift(-lookahead)
        current_prices = data['close']
        
        # Target: 1 if price goes up, 0 if price goes down
        target = (future_prices > current_prices).astype(int)
        
        return target
    
    def train(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Train the Random Forest model."""
        try:
            # Prepare features
            features_df = self.prepare_features(data)
            
            # Create target
            target = self.create_target(features_df)
            
            # Select feature columns (exclude target and timestamp columns)
            exclude_cols = ['timestamp', 'target', 'close', 'open', 'high', 'low']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            X = features_df[feature_cols]
            y = target
            
            # Remove rows with NaN or infinite values
            mask = ~(X.isna().any(axis=1) | y.isna() | X.isin([np.inf, -np.inf]).any(axis=1))
            X = X[mask]
            y = y[mask]
            
            # Replace any remaining infinite values with NaN and drop them
            X = X.replace([np.inf, -np.inf], np.nan).dropna()
            y = y[X.index]
            
            if len(X) == 0:
                self.log.error("No valid data for training")
                return {'success': False, 'error': 'No valid data'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=self.config.RF_N_ESTIMATORS,
                max_depth=self.config.RF_MAX_DEPTH,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Set feature columns before saving
            self.feature_columns = feature_cols
            
            # Save model
            self._save_model()
            
            self.log.info(f"Model trained successfully. Accuracy: {accuracy:.3f}")
            
            return {
                'success': True,
                'accuracy': accuracy,
                'feature_importance': dict(zip(feature_cols, self.model.feature_importances_))
            }
            
        except Exception as e:
            self.log.error(f"Error training model: {e}")
            return {'success': False, 'error': str(e)}
    
    def predict(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Make prediction using the trained model."""
        if self.model is None:
            self.log.warning("Model not trained. Cannot make predictions.")
            return None
        
        try:
            # Prepare features
            features_df = self.prepare_features(data)
            
            # Get latest valid data point (without NaN or infinite values)
            latest = features_df.iloc[-1:]
            
            # Check if latest data has NaN or infinite values in feature columns
            feature_data = latest[self.feature_columns]
            has_invalid = (feature_data.isnull().any().any() or 
                          feature_data.isin([np.inf, -np.inf]).any().any())
            
            if has_invalid:
                # Try to get the most recent valid data point
                valid_data = features_df[self.feature_columns].dropna()
                # Remove infinite values
                valid_data = valid_data.replace([np.inf, -np.inf], np.nan).dropna()
                
                if len(valid_data) == 0:
                    self.log.warning("No valid data points for prediction")
                    return None
                latest = valid_data.iloc[-1:].copy()
            
            # Select features and ensure no infinite values
            X = latest[self.feature_columns].copy()
            
            # Final cleanup: replace any remaining infinite values with 0
            X = X.replace([np.inf, -np.inf], 0)
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0]
            
            return {
                'prediction': int(prediction),
                'probability': float(probability[1]),  # Probability of up movement
                'confidence': float(max(probability))
            }
            
        except Exception as e:
            self.log.error(f"Error making prediction: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, lower
    
    def _save_model(self):
        """Save the trained model."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'feature_columns': self.feature_columns
            }, self.model_path)
            self.log.info(f"Model saved to {self.model_path}")
        except Exception as e:
            self.log.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load existing model if available."""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.feature_columns = model_data['feature_columns']
                self.log.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            self.log.warning(f"Could not load existing model: {e}")
    
    def validate(self) -> bool:
        """Validate ML model configuration."""
        try:
            # Check if model exists or can be created
            if self.model is None:
                self.log.warning("ML model not trained yet")
                return True  # Not an error, just not trained
            return True
        except Exception as e:
            self.log.error(f"ML model validation failed: {e}")
            return False
