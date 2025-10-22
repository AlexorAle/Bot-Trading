"""
Backup Manager - Sistema de backup periódico
"""

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone
import shutil
import gzip

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor de backups periódicos"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backup_config = config.get('backup', {})
        
        # Configuración de backup
        self.enabled = self.backup_config.get('enabled', True)
        self.interval_minutes = self.backup_config.get('interval_minutes', 30)
        self.max_backups = self.backup_config.get('max_backups', 100)
        self.backup_path = Path(self.backup_config.get('backup_path', 'backups/'))
        
        # Crear directorio de backup si no existe
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Estado del backup
        self.last_backup_time = 0
        self.backup_count = 0
        self.is_running = False
        
        logger.info(f"BackupManager initialized - Interval: {self.interval_minutes}min, Max backups: {self.max_backups}")
    
    async def start_backup_service(self, paper_trader, risk_manager):
        """Iniciar servicio de backup periódico"""
        if not self.enabled:
            logger.info("Backup service disabled")
            return
        
        self.is_running = True
        logger.info("Backup service started")
        
        try:
            while self.is_running:
                await asyncio.sleep(self.interval_minutes * 60)  # Convertir a segundos
                
                if self.is_running:
                    await self._perform_backup(paper_trader, risk_manager)
                    
        except asyncio.CancelledError:
            logger.info("Backup service cancelled")
        except Exception as e:
            logger.error(f"Error in backup service: {e}")
        finally:
            self.is_running = False
    
    async def _perform_backup(self, paper_trader, risk_manager):
        """Realizar backup completo"""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_path / f"backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            logger.info(f"Starting backup: {backup_dir}")
            
            # 1. Backup de posiciones y balance
            await self._backup_trading_data(paper_trader, backup_dir)
            
            # 2. Backup de métricas de riesgo
            await self._backup_risk_data(risk_manager, backup_dir)
            
            # 3. Backup de configuración
            await self._backup_configuration(backup_dir)
            
            # 4. Backup de logs
            await self._backup_logs(backup_dir)
            
            # 5. Crear archivo de resumen
            await self._create_backup_summary(backup_dir, paper_trader, risk_manager)
            
            # 6. Comprimir backup
            await self._compress_backup(backup_dir)
            
            # 7. Limpiar backups antiguos
            await self._cleanup_old_backups()
            
            self.last_backup_time = time.time()
            self.backup_count += 1
            
            logger.info(f"Backup completed: {backup_dir}")
            
        except Exception as e:
            logger.error(f"Error performing backup: {e}")
    
    async def _backup_trading_data(self, paper_trader, backup_dir: Path):
        """Backup de datos de trading"""
        try:
            trading_data = {
                'timestamp': time.time(),
                'balance': paper_trader.balance,
                'initial_balance': paper_trader.initial_balance,
                'positions': {
                    symbol: {
                        'size': pos.size,
                        'side': pos.side,
                        'entry_price': pos.entry_price,
                        'unrealized_pnl': pos.unrealized_pnl,
                        'timestamp': pos.timestamp
                    }
                    for symbol, pos in paper_trader.positions.items()
                },
                'orders': [
                    {
                        'order_id': order.order_id,
                        'symbol': order.symbol,
                        'side': order.side,
                        'qty': order.qty,
                        'price': order.price,
                        'status': order.status,
                        'timestamp': order.timestamp
                    }
                    for order in paper_trader.orders.values()
                ],
                'trades': [
                    {
                        'trade_id': trade.trade_id,
                        'order_id': trade.order_id,
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'qty': trade.qty,
                        'price': trade.price,
                        'commission': trade.commission,
                        'timestamp': trade.timestamp
                    }
                    for trade in paper_trader.trades
                ],
                'current_prices': paper_trader.current_prices,
                'total_trades': len(paper_trader.trades),
                'total_pnl': sum(trade.pnl for trade in paper_trader.trades)
            }
            
            with open(backup_dir / 'trading_data.json', 'w') as f:
                json.dump(trading_data, f, indent=2)
            
            logger.info("Trading data backed up")
            
        except Exception as e:
            logger.error(f"Error backing up trading data: {e}")
    
    async def _backup_risk_data(self, risk_manager, backup_dir: Path):
        """Backup de datos de riesgo"""
        try:
            risk_data = risk_manager.get_risk_status()
            risk_data['backup_timestamp'] = time.time()
            
            with open(backup_dir / 'risk_data.json', 'w') as f:
                json.dump(risk_data, f, indent=2)
            
            logger.info("Risk data backed up")
            
        except Exception as e:
            logger.error(f"Error backing up risk data: {e}")
    
    async def _backup_configuration(self, backup_dir: Path):
        """Backup de configuración"""
        try:
            config_dir = Path('configs')
            if config_dir.exists():
                backup_config_dir = backup_dir / 'configs'
                backup_config_dir.mkdir(exist_ok=True)
                
                for config_file in config_dir.glob('*.json'):
                    shutil.copy2(config_file, backup_config_dir / config_file.name)
                
                logger.info("Configuration backed up")
            
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
    
    async def _backup_logs(self, backup_dir: Path):
        """Backup de logs recientes"""
        try:
            log_files = []
            
            # Buscar archivos de log
            for log_file in Path('.').glob('*.log'):
                if log_file.stat().st_size > 0:
                    log_files.append(log_file)
            
            if log_files:
                logs_dir = backup_dir / 'logs'
                logs_dir.mkdir(exist_ok=True)
                
                for log_file in log_files:
                    # Copiar solo las últimas 1000 líneas
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                    
                    with open(logs_dir / log_file.name, 'w', encoding='utf-8') as f:
                        f.writelines(recent_lines)
                
                logger.info(f"Logs backed up: {len(log_files)} files")
            
        except Exception as e:
            logger.error(f"Error backing up logs: {e}")
    
    async def _create_backup_summary(self, backup_dir: Path, paper_trader, risk_manager):
        """Crear resumen del backup"""
        try:
            summary = {
                'backup_timestamp': time.time(),
                'backup_date': datetime.now(timezone.utc).isoformat(),
                'trading_summary': {
                    'balance': paper_trader.balance,
                    'initial_balance': paper_trader.initial_balance,
                    'total_pnl': paper_trader.balance - paper_trader.initial_balance,
                    'pnl_percentage': ((paper_trader.balance - paper_trader.initial_balance) / paper_trader.initial_balance) * 100,
                    'total_trades': len(paper_trader.trades),
                    'active_positions': len(paper_trader.positions),
                    'total_orders': len(paper_trader.orders)
                },
                'risk_summary': {
                    'daily_trades': risk_manager.daily_stats.get('trades_count', 0),
                    'daily_pnl': risk_manager.daily_stats.get('total_pnl', 0),
                    'max_drawdown': risk_manager.daily_stats.get('max_drawdown', 0),
                    'market_conditions_count': len(risk_manager.market_conditions)
                },
                'system_info': {
                    'backup_count': self.backup_count,
                    'last_backup_interval': self.interval_minutes,
                    'max_backups': self.max_backups
                }
            }
            
            with open(backup_dir / 'backup_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info("Backup summary created")
            
        except Exception as e:
            logger.error(f"Error creating backup summary: {e}")
    
    async def _compress_backup(self, backup_dir: Path):
        """Comprimir backup"""
        try:
            compressed_file = f"{backup_dir}.tar.gz"
            
            # Crear archivo comprimido
            shutil.make_archive(str(backup_dir), 'gztar', backup_dir.parent, backup_dir.name)
            
            # Eliminar directorio original
            shutil.rmtree(backup_dir)
            
            logger.info(f"Backup compressed: {compressed_file}")
            
        except Exception as e:
            logger.error(f"Error compressing backup: {e}")
    
    async def _cleanup_old_backups(self):
        """Limpiar backups antiguos"""
        try:
            backup_files = list(self.backup_path.glob('backup_*.tar.gz'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(backup_files) > self.max_backups:
                files_to_delete = backup_files[self.max_backups:]
                
                for file_to_delete in files_to_delete:
                    file_to_delete.unlink()
                    logger.info(f"Deleted old backup: {file_to_delete.name}")
                
                logger.info(f"Cleaned up {len(files_to_delete)} old backups")
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def stop_backup_service(self):
        """Detener servicio de backup"""
        self.is_running = False
        logger.info("Backup service stopped")
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Obtener estado del backup"""
        return {
            'enabled': self.enabled,
            'is_running': self.is_running,
            'interval_minutes': self.interval_minutes,
            'max_backups': self.max_backups,
            'backup_count': self.backup_count,
            'last_backup_time': self.last_backup_time,
            'backup_path': str(self.backup_path),
            'available_backups': len(list(self.backup_path.glob('backup_*.tar.gz')))
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Listar backups disponibles"""
        backups = []
        
        try:
            backup_files = list(self.backup_path.glob('backup_*.tar.gz'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': str(backup_file)
                })
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    async def restore_backup(self, backup_filename: str) -> bool:
        """Restaurar backup"""
        try:
            backup_file = self.backup_path / backup_filename
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Extraer backup
            extract_dir = self.backup_path / f"restore_{int(time.time())}"
            shutil.unpack_archive(backup_file, extract_dir, 'gztar')
            
            logger.info(f"Backup restored to: {extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
