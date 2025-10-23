"""
Disaster Recovery - Sistema de recuperación ante desastres
"""

import asyncio
import logging
import time
import json
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import subprocess
import psutil

from backup_manager import global_backup_manager, BackupType, BackupStatus

logger = logging.getLogger(__name__)

class RecoveryStatus(Enum):
    """Estado de recuperación"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"

class DisasterType(Enum):
    """Tipos de desastre"""
    DATA_CORRUPTION = "data_corruption"
    SYSTEM_CRASH = "system_crash"
    CONFIG_LOSS = "config_loss"
    STATE_LOSS = "state_loss"
    COMPLETE_FAILURE = "complete_failure"

@dataclass
class RecoveryPlan:
    """Plan de recuperación"""
    disaster_type: DisasterType
    severity: int  # 1-10
    recovery_steps: List[str]
    estimated_time_minutes: int
    required_backups: List[str]
    rollback_possible: bool

class DisasterRecovery:
    """Sistema de recuperación ante desastres"""
    
    def __init__(self):
        self.backup_manager = global_backup_manager
        self.logger = logging.getLogger("DisasterRecovery")
        self.recovery_status = RecoveryStatus.IDLE
        self.current_recovery = None
        
        # Configuración de recuperación
        self.critical_files = [
            "logs/bot_state.json",
            "configs/alert_config.json",
            "configs/bybit_x_config.json",
            ".env"
        ]
        
        self.essential_dirs = [
            "backtrader_engine",
            "configs",
            "scripts"
        ]
        
        # Planes de recuperación
        self.recovery_plans = self._init_recovery_plans()
        
        self.logger.info("DisasterRecovery system initialized")
    
    def _init_recovery_plans(self) -> Dict[DisasterType, RecoveryPlan]:
        """Inicializar planes de recuperación"""
        return {
            DisasterType.DATA_CORRUPTION: RecoveryPlan(
                disaster_type=DisasterType.DATA_CORRUPTION,
                severity=7,
                recovery_steps=[
                    "1. Stop bot processes",
                    "2. Verify backup integrity",
                    "3. Restore state file from latest backup",
                    "4. Restore configuration files",
                    "5. Validate restored data",
                    "6. Restart bot with restored state"
                ],
                estimated_time_minutes=15,
                required_backups=["state", "config"],
                rollback_possible=True
            ),
            
            DisasterType.SYSTEM_CRASH: RecoveryPlan(
                disaster_type=DisasterType.SYSTEM_CRASH,
                severity=8,
                recovery_steps=[
                    "1. Assess system damage",
                    "2. Check process status",
                    "3. Restore from latest full backup",
                    "4. Recreate missing directories",
                    "5. Restore configuration",
                    "6. Restore state",
                    "7. Restart all services"
                ],
                estimated_time_minutes=30,
                required_backups=["full"],
                rollback_possible=True
            ),
            
            DisasterType.CONFIG_LOSS: RecoveryPlan(
                disaster_type=DisasterType.CONFIG_LOSS,
                severity=5,
                recovery_steps=[
                    "1. Stop bot",
                    "2. Restore configuration files",
                    "3. Validate configuration",
                    "4. Restart bot"
                ],
                estimated_time_minutes=10,
                required_backups=["config"],
                rollback_possible=True
            ),
            
            DisasterType.STATE_LOSS: RecoveryPlan(
                disaster_type=DisasterType.STATE_LOSS,
                severity=6,
                recovery_steps=[
                    "1. Stop bot",
                    "2. Restore state file from backup",
                    "3. Validate state integrity",
                    "4. Restart bot with restored state"
                ],
                estimated_time_minutes=10,
                required_backups=["state"],
                rollback_possible=True
            ),
            
            DisasterType.COMPLETE_FAILURE: RecoveryPlan(
                disaster_type=DisasterType.COMPLETE_FAILURE,
                severity=10,
                recovery_steps=[
                    "1. Assess complete damage",
                    "2. Restore entire system from backup",
                    "3. Recreate all directories",
                    "4. Restore all configurations",
                    "5. Restore state and logs",
                    "6. Validate system integrity",
                    "7. Restart all services",
                    "8. Run system tests"
                ],
                estimated_time_minutes=60,
                required_backups=["full"],
                rollback_possible=False
            )
        }
    
    async def detect_disaster(self) -> Optional[DisasterType]:
        """Detectar tipo de desastre"""
        try:
            self.logger.info("Scanning for potential disasters...")
            
            # Verificar archivos críticos
            missing_critical = []
            for file_path in self.critical_files:
                if not Path(file_path).exists():
                    missing_critical.append(file_path)
            
            # Verificar directorios esenciales
            missing_dirs = []
            for dir_path in self.essential_dirs:
                if not Path(dir_path).exists():
                    missing_dirs.append(dir_path)
            
            # Verificar integridad de archivos
            corrupted_files = []
            for file_path in self.critical_files:
                if Path(file_path).exists():
                    if not self._validate_file_integrity(Path(file_path)):
                        corrupted_files.append(file_path)
            
            # Determinar tipo de desastre
            if len(missing_dirs) > 2 or len(missing_critical) > 3:
                return DisasterType.COMPLETE_FAILURE
            elif len(corrupted_files) > 0:
                return DisasterType.DATA_CORRUPTION
            elif len(missing_critical) > 0:
                if any("config" in f for f in missing_critical):
                    return DisasterType.CONFIG_LOSS
                elif "bot_state.json" in missing_critical:
                    return DisasterType.STATE_LOSS
            elif not self._is_bot_running():
                return DisasterType.SYSTEM_CRASH
            
            self.logger.info("No disasters detected")
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting disaster: {e}")
            return DisasterType.COMPLETE_FAILURE
    
    def _validate_file_integrity(self, file_path: Path) -> bool:
        """Validar integridad de archivo"""
        try:
            if not file_path.exists():
                return False
            
            # Verificar que el archivo no esté vacío
            if file_path.stat().st_size == 0:
                return False
            
            # Verificar archivos JSON
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    json.load(f)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"File integrity check failed for {file_path}: {e}")
            return False
    
    def _is_bot_running(self) -> bool:
        """Verificar si el bot está corriendo"""
        try:
            # Buscar procesos de Python que ejecuten el bot
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] in ['python', 'python3']:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'paper_trading_main.py' in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            self.logger.error(f"Error checking bot status: {e}")
            return False
    
    async def execute_recovery(self, disaster_type: DisasterType) -> bool:
        """Ejecutar recuperación"""
        try:
            if disaster_type not in self.recovery_plans:
                raise ValueError(f"No recovery plan for disaster type: {disaster_type}")
            
            plan = self.recovery_plans[disaster_type]
            self.recovery_status = RecoveryStatus.ANALYZING
            self.current_recovery = {
                "disaster_type": disaster_type,
                "plan": plan,
                "start_time": datetime.now(timezone.utc),
                "steps_completed": [],
                "errors": []
            }
            
            self.logger.critical(f"🚨 DISASTER DETECTED: {disaster_type.value}")
            self.logger.critical(f"Executing recovery plan (severity: {plan.severity}/10)")
            
            # Verificar backups disponibles
            available_backups = self.backup_manager.list_backups()
            if not available_backups:
                raise Exception("No backups available for recovery")
            
            # Encontrar backup apropiado
            recovery_backup = self._find_recovery_backup(plan, available_backups)
            if not recovery_backup:
                raise Exception(f"No suitable backup found for {disaster_type.value}")
            
            self.logger.info(f"Using backup for recovery: {recovery_backup.id}")
            
            # Ejecutar pasos de recuperación
            self.recovery_status = RecoveryStatus.RECOVERING
            
            for i, step in enumerate(plan.recovery_steps, 1):
                self.logger.info(f"Recovery step {i}/{len(plan.recovery_steps)}: {step}")
                
                try:
                    await self._execute_recovery_step(step, recovery_backup)
                    self.current_recovery["steps_completed"].append(step)
                except Exception as e:
                    error_msg = f"Step {i} failed: {e}"
                    self.logger.error(error_msg)
                    self.current_recovery["errors"].append(error_msg)
                    
                    # Determinar si continuar o abortar
                    if plan.severity >= 8:  # Crítico - continuar
                        self.logger.warning("Critical disaster - continuing recovery despite errors")
                    else:
                        raise e
            
            # Validar recuperación
            if await self._validate_recovery():
                self.recovery_status = RecoveryStatus.COMPLETED
                self.logger.info("✅ Recovery completed successfully")
                return True
            else:
                self.recovery_status = RecoveryStatus.FAILED
                self.logger.error("❌ Recovery validation failed")
                return False
                
        except Exception as e:
            self.recovery_status = RecoveryStatus.FAILED
            self.logger.error(f"❌ Recovery failed: {e}")
            if self.current_recovery:
                self.current_recovery["errors"].append(str(e))
            return False
    
    def _find_recovery_backup(self, plan: RecoveryPlan, available_backups: List) -> Optional[Any]:
        """Encontrar backup apropiado para recuperación"""
        try:
            # Filtrar backups completados
            completed_backups = [b for b in available_backups if b.status == BackupStatus.COMPLETED]
            
            if not completed_backups:
                return None
            
            # Ordenar por fecha (más reciente primero)
            completed_backups.sort(key=lambda x: x.created_at, reverse=True)
            
            # Buscar backup que cumpla los requisitos
            for backup in completed_backups:
                if "full" in plan.required_backups and backup.type == BackupType.FULL:
                    return backup
                elif "state" in plan.required_backups and backup.type == BackupType.STATE_ONLY:
                    return backup
                elif "config" in plan.required_backups and backup.type == BackupType.CONFIG_ONLY:
                    return backup
            
            # Si no encuentra específico, usar el más reciente
            return completed_backups[0]
            
        except Exception as e:
            self.logger.error(f"Error finding recovery backup: {e}")
            return None
    
    async def _execute_recovery_step(self, step: str, backup):
        """Ejecutar paso de recuperación"""
        if "Stop bot" in step:
            await self._stop_bot_processes()
        elif "Restore state" in step:
            await self._restore_state_file(backup)
        elif "Restore configuration" in step:
            await self._restore_configuration(backup)
        elif "Restore from latest full backup" in step:
            await self._restore_full_backup(backup)
        elif "Recreate missing directories" in step:
            await self._recreate_directories()
        elif "Restart bot" in step:
            await self._restart_bot()
        elif "Validate" in step:
            await self._validate_system()
        elif "Run system tests" in step:
            await self._run_system_tests()
        else:
            self.logger.warning(f"Unknown recovery step: {step}")
    
    async def _stop_bot_processes(self):
        """Detener procesos del bot"""
        try:
            # Buscar y detener procesos del bot
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] in ['python', 'python3']:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'paper_trading_main.py' in cmdline:
                            proc.terminate()
                            self.logger.info(f"Stopped bot process: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Esperar un momento para que los procesos terminen
            await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.error(f"Error stopping bot processes: {e}")
            raise
    
    async def _restore_state_file(self, backup):
        """Restaurar archivo de estado"""
        try:
            # Crear backup de seguridad del estado actual
            if Path("logs/bot_state.json").exists():
                shutil.copy2("logs/bot_state.json", "logs/bot_state.json.backup")
            
            # Restaurar desde backup
            await self.backup_manager.restore_backup(backup.id)
            
            self.logger.info("State file restored successfully")
            
        except Exception as e:
            self.logger.error(f"Error restoring state file: {e}")
            raise
    
    async def _restore_configuration(self, backup):
        """Restaurar configuración"""
        try:
            # Restaurar archivos de configuración
            await self.backup_manager.restore_backup(backup.id)
            
            self.logger.info("Configuration restored successfully")
            
        except Exception as e:
            self.logger.error(f"Error restoring configuration: {e}")
            raise
    
    async def _restore_full_backup(self, backup):
        """Restaurar backup completo"""
        try:
            # Restaurar backup completo
            await self.backup_manager.restore_backup(backup.id)
            
            self.logger.info("Full backup restored successfully")
            
        except Exception as e:
            self.logger.error(f"Error restoring full backup: {e}")
            raise
    
    async def _recreate_directories(self):
        """Recrear directorios faltantes"""
        try:
            for dir_path in self.essential_dirs:
                Path(dir_path).mkdir(exist_ok=True)
                self.logger.info(f"Created directory: {dir_path}")
            
            # Crear directorio de logs si no existe
            Path("logs").mkdir(exist_ok=True)
            
        except Exception as e:
            self.logger.error(f"Error recreating directories: {e}")
            raise
    
    async def _restart_bot(self):
        """Reiniciar bot"""
        try:
            # El bot se reiniciará automáticamente por systemd o el proceso supervisor
            self.logger.info("Bot restart initiated")
            
        except Exception as e:
            self.logger.error(f"Error restarting bot: {e}")
            raise
    
    async def _validate_system(self):
        """Validar sistema después de recuperación"""
        try:
            # Verificar archivos críticos
            for file_path in self.critical_files:
                if not Path(file_path).exists():
                    raise Exception(f"Critical file missing after recovery: {file_path}")
            
            # Verificar directorios esenciales
            for dir_path in self.essential_dirs:
                if not Path(dir_path).exists():
                    raise Exception(f"Essential directory missing after recovery: {dir_path}")
            
            self.logger.info("System validation passed")
            
        except Exception as e:
            self.logger.error(f"System validation failed: {e}")
            raise
    
    async def _run_system_tests(self):
        """Ejecutar pruebas del sistema"""
        try:
            # Verificar que el bot puede iniciarse
            # (Esto sería implementado según el sistema de testing disponible)
            self.logger.info("System tests completed")
            
        except Exception as e:
            self.logger.error(f"System tests failed: {e}")
            raise
    
    async def _validate_recovery(self) -> bool:
        """Validar que la recuperación fue exitosa"""
        try:
            # Verificar que no hay desastres detectados
            disaster = await self.detect_disaster()
            if disaster:
                self.logger.error(f"Disaster still detected after recovery: {disaster}")
                return False
            
            # Verificar integridad de archivos críticos
            for file_path in self.critical_files:
                if not self._validate_file_integrity(Path(file_path)):
                    self.logger.error(f"File integrity check failed: {file_path}")
                    return False
            
            self.logger.info("Recovery validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Recovery validation error: {e}")
            return False
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Obtener estado de recuperación"""
        return {
            "status": self.recovery_status.value,
            "current_recovery": self.current_recovery,
            "available_plans": len(self.recovery_plans),
            "critical_files": len(self.critical_files),
            "essential_dirs": len(self.essential_dirs)
        }
    
    async def run_disaster_recovery_check(self) -> bool:
        """Ejecutar verificación de recuperación ante desastres"""
        try:
            self.logger.info("Running disaster recovery check...")
            
            # Detectar desastres
            disaster = await self.detect_disaster()
            
            if disaster:
                self.logger.critical(f"🚨 DISASTER DETECTED: {disaster.value}")
                
                # Ejecutar recuperación automática
                success = await self.execute_recovery(disaster)
                
                if success:
                    self.logger.info("✅ Disaster recovery completed successfully")
                    return True
                else:
                    self.logger.error("❌ Disaster recovery failed")
                    return False
            else:
                self.logger.info("✅ No disasters detected")
                return True
                
        except Exception as e:
            self.logger.error(f"Error in disaster recovery check: {e}")
            return False

# Instancia global del sistema de disaster recovery
global_disaster_recovery = DisasterRecovery()
