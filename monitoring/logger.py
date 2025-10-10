"""
Bot logging and monitoring utilities.
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import os


class BotLogger:
    """Bot logging and monitoring utilities."""
    
    def __init__(self):
        """Initialize the bot logger."""
        self.log = logging.getLogger(__name__)
        self.trades_log = []
        self.performance_log = []
    
    def log_trade(self, trade_result: Dict[str, Any]) -> None:
        """Log a trade result."""
        try:
            if trade_result is None:
                return
            
            # Add timestamp if not present
            if 'timestamp' not in trade_result:
                trade_result['timestamp'] = datetime.now()
            
            # Store trade
            self.trades_log.append(trade_result)
            
            # Log to file
            self.log.info(f"Trade logged: {trade_result}")
            
            # Update performance metrics
            self._update_performance_metrics(trade_result)
            
        except Exception as e:
            self.log.error(f"Error logging trade: {e}")
    
    def _update_performance_metrics(self, trade_result: Dict[str, Any]) -> None:
        """Update performance metrics."""
        try:
            # Calculate basic metrics
            total_trades = len(self.trades_log)
            winning_trades = len([t for t in self.trades_log if t.get('pnl', 0) > 0])
            losing_trades = len([t for t in self.trades_log if t.get('pnl', 0) < 0])
            
            # Calculate win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate total P&L
            total_pnl = sum(t.get('pnl', 0) for t in self.trades_log)
            
            # Store performance metrics
            performance = {
                'timestamp': datetime.now(),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl
            }
            
            self.performance_log.append(performance)
            
        except Exception as e:
            self.log.error(f"Error updating performance metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            if not self.trades_log:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_trade_pnl': 0
                }
            
            total_trades = len(self.trades_log)
            winning_trades = len([t for t in self.trades_log if t.get('pnl', 0) > 0])
            total_pnl = sum(t.get('pnl', 0) for t in self.trades_log)
            
            return {
                'total_trades': total_trades,
                'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0
            }
            
        except Exception as e:
            self.log.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_recent_trades(self, n: int = 10) -> list:
        """Get recent trades."""
        try:
            return self.trades_log[-n:] if len(self.trades_log) >= n else self.trades_log
        except Exception as e:
            self.log.error(f"Error getting recent trades: {e}")
            return []
    
    def export_trades_to_csv(self, filename: Optional[str] = None) -> str:
        """Export trades to CSV file."""
        try:
            if filename is None:
                filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Create DataFrame
            df = pd.DataFrame(self.trades_log)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            self.log.info(f"Trades exported to {filename}")
            return filename
            
        except Exception as e:
            self.log.error(f"Error exporting trades: {e}")
            return ""
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        try:
            self.trades_log.clear()
            self.performance_log.clear()
            self.log.info("All logs cleared")
        except Exception as e:
            self.log.error(f"Error clearing logs: {e}")




