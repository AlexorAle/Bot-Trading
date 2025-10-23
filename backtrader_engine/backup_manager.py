"""
Backup Manager - Sistema completo de backup y recovery
"""

import os
import shutil
import json
import gzip
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import threading
import hashlib
import tarfile
from enum import Enum

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Tipos de backup"""
    FULL = "full"
    INCREMENTAL = "incremental"
    STATE_ONLY = "state_only"
    CONFIG_ONLY = "config_only"
    LOGS_ONLY = "logs_only"

class BackupStatus(Enum):
    """Estado de backup"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"

@dataclass
class BackupInfo:
    """Información de backup"""
    id: str
    type: BackupType
    status: BackupStatus
    created_at: datetime
    size_bytes: int
    file_path: str
    checksum: str
    description: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BackupManager:
    """Gestor de backups del bot de trading"""
    
    def __init__(self, 
                 backup_dir: str = "backups",
                 max_backups: int = 30,
                 compression: bool = True,
                 encryption_key: Optional[str] = None):
        
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.compression = compression
        self.encryption_key = encryption_key
        self.lock = threading.Lock()
        self.logger = logging.getLogger("BackupManager")
        
        # Crear directorio de backups
        self.backup_dir.mkdir(exist_ok=True)
        
        # Archivo de índice de backups
        self.index_file = self.backup_dir / "backup_index.json"
        self.backups: Dict[str, BackupInfo] = {}
        
        # Cargar índice existente
        self._load_backup_index()
        
        # Configuración de archivos a respaldar
        self.backup_paths = {
            "state": "logs/bot_state.json",
            "configs": "configs/",
            "logs": "logs/",
            "scripts": "scripts/",
            "backtrader_engine": "backtrader_engine/",
            "streamlit_dashboard": "streamlit_dashboard_modern.py",
            "investment_manager": "investment_manager.py"
        }
        
        self.logger.info(f"BackupManager initialized - Backup dir: {self.backup_dir}")
    
    def _load_backup_index(self):
        """Cargar índice de backups"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                
                for backup_id, backup_data in data.items():
                    backup_data['created_at'] = datetime.fromisoformat(backup_data['created_at'])
                    backup_data['type'] = BackupType(backup_data['type'])
                    backup_data['status'] = BackupStatus(backup_data['status'])
                    self.backups[backup_id] = BackupInfo(**backup_data)
                
                self.logger.info(f"Loaded {len(self.backups)} backups from index")
        except Exception as e:
            self.logger.error(f"Error loading backup index: {e}")
            self.backups = {}
    
    def _save_backup_index(self):
        """Guardar índice de backups"""
        try:
            with self.lock:
                data = {}
                for backup_id, backup in self.backups.items():
                    backup_dict = asdict(backup)
                    backup_dict['created_at'] = backup.created_at.isoformat()
                    backup_dict['type'] = backup.type.value
                    backup_dict['status'] = backup.status.value
                    data[backup_id] = backup_dict
                
                with open(self.index_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.logger.debug("Backup index saved")
        except Exception as e:
            self.logger.error(f"Error saving backup index: {e}")
    
    def _generate_backup_id(self, backup_type: BackupType) -> str:
        """Generar ID único para backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{backup_type.value}_{timestamp}"
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcular checksum de archivo"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def _get_file_size(self, file_path: Path) -> int:
        """Obtener tamaño de archivo"""
        try:
            return file_path.stat().st_size
        except:
            return 0
    
    async def create_backup(self, 
                           backup_type: BackupType = BackupType.FULL,
                           description: str = "",
                           include_logs: bool = True) -> str:
        """Crear backup"""
        backup_id = self._generate_backup_id(backup_type)
        
        try:
            self.logger.info(f"Creating {backup_type.value} backup: {backup_id}")
            
            # Crear información de backup
            backup_info = BackupInfo(
                id=backup_id,
                type=backup_type,
                status=BackupStatus.IN_PROGRESS,
                created_at=datetime.now(timezone.utc),
                size_bytes=0,
                file_path="",
                checksum="",
                description=description
            )
            
            # Determinar archivos a respaldar
            files_to_backup = self._get_files_to_backup(backup_type, include_logs)
            
            # Crear archivo de backup
            backup_file = self.backup_dir / f"{backup_id}.tar"
            if self.compression:
                backup_file = self.backup_dir / f"{backup_id}.tar.gz"
            
            # Crear backup
            await self._create_backup_file(backup_file, files_to_backup, backup_info)
            
            # Actualizar información
            backup_info.file_path = str(backup_file)
            backup_info.size_bytes = self._get_file_size(backup_file)
            backup_info.checksum = self._calculate_checksum(backup_file)
            backup_info.status = BackupStatus.COMPLETED
            
            # Guardar en índice
            with self.lock:
                self.backups[backup_id] = backup_info
                self._save_backup_index()
            
            # Limpiar backups antiguos
            self._cleanup_old_backups()
            
            self.logger.info(f"Backup created successfully: {backup_id} ({backup_info.size_bytes} bytes)")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Error creating backup {backup_id}: {e}")
            if backup_id in self.backups:
                self.backups[backup_id].status = BackupStatus.FAILED
                self._save_backup_index()
            raise
    
    def _get_files_to_backup(self, backup_type: BackupType, include_logs: bool) -> List[Path]:
        """Obtener archivos a respaldar según tipo"""
        files = []
        project_root = Path.cwd()
        
        if backup_type == BackupType.FULL:
            # Respaldar todo
            for name, path in self.backup_paths.items():
                full_path = project_root / path
                if full_path.exists():
                    files.append(full_path)
        
        elif backup_type == BackupType.STATE_ONLY:
            # Solo estado del bot
            state_file = project_root / self.backup_paths["state"]
            if state_file.exists():
                files.append(state_file)
        
        elif backup_type == BackupType.CONFIG_ONLY:
            # Solo configuraciones
            config_dir = project_root / self.backup_paths["configs"]
            if config_dir.exists():
                files.append(config_dir)
        
        elif backup_type == BackupType.LOGS_ONLY:
            # Solo logs
            if include_logs:
                logs_dir = project_root / self.backup_paths["logs"]
                if logs_dir.exists():
                    files.append(logs_dir)
        
        elif backup_type == BackupType.INCREMENTAL:
            # Backup incremental (archivos modificados en las últimas 24 horas)
            cutoff_time = time.time() - (24 * 3600)  # 24 horas
            
            for name, path in self.backup_paths.items():
                full_path = project_root / path
                if full_path.exists():
                    if full_path.is_file():
                        if full_path.stat().st_mtime > cutoff_time:
                            files.append(full_path)
                    else:
                        # Directorio - agregar archivos modificados
                        for file_path in full_path.rglob("*"):
                            if file_path.is_file() and file_path.stat().st_mtime > cutoff_time:
                                files.append(file_path)
        
        return files
    
    async def _create_backup_file(self, backup_file: Path, files: List[Path], backup_info: BackupInfo):
        """Crear archivo de backup"""
        try:
            # Crear archivo tar
            mode = "w:gz" if self.compression else "w"
            
            with tarfile.open(backup_file, mode) as tar:
                # Agregar archivos
                for file_path in files:
                    if file_path.exists():
                        arcname = file_path.relative_to(Path.cwd())
                        tar.add(file_path, arcname=arcname)
                        self.logger.debug(f"Added to backup: {arcname}")
                
                # Agregar metadatos
                metadata = {
                    "backup_id": backup_info.id,
                    "backup_type": backup_info.type.value,
                    "created_at": backup_info.created_at.isoformat(),
                    "description": backup_info.description,
                    "files_count": len(files),
                    "compression": self.compression
                }
                
                # Crear archivo temporal con metadatos
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    json.dump(metadata, tmp, indent=2)
                    tmp_path = tmp.name
                
                tar.add(tmp_path, arcname="backup_metadata.json")
                os.unlink(tmp_path)  # Eliminar archivo temporal
            
            self.logger.info(f"Backup file created: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating backup file: {e}")
            raise
    
    async def restore_backup(self, backup_id: str, target_dir: Optional[Path] = None) -> bool:
        """Restaurar backup"""
        try:
            if backup_id not in self.backups:
                raise ValueError(f"Backup {backup_id} not found")
            
            backup_info = self.backups[backup_id]
            
            if backup_info.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup {backup_id} is not completed")
            
            backup_file = Path(backup_info.file_path)
            if not backup_file.exists():
                raise ValueError(f"Backup file not found: {backup_file}")
            
            # Verificar checksum
            current_checksum = self._calculate_checksum(backup_file)
            if current_checksum != backup_info.checksum:
                self.logger.warning(f"Checksum mismatch for backup {backup_id}")
                backup_info.status = BackupStatus.CORRUPTED
                self._save_backup_index()
                raise ValueError("Backup file is corrupted")
            
            self.logger.info(f"Restoring backup: {backup_id}")
            
            # Directorio de destino
            if target_dir is None:
                target_dir = Path.cwd()
            
            # Crear backup de seguridad antes de restaurar
            safety_backup_id = await self.create_backup(
                BackupType.FULL, 
                f"Safety backup before restoring {backup_id}"
            )
            self.logger.info(f"Created safety backup: {safety_backup_id}")
            
            # Extraer backup
            await self._extract_backup(backup_file, target_dir)
            
            self.logger.info(f"Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup {backup_id}: {e}")
            return False
    
    async def _extract_backup(self, backup_file: Path, target_dir: Path):
        """Extraer archivos del backup"""
        try:
            # Determinar modo de apertura
            if backup_file.suffix == '.gz':
                mode = "r:gz"
            else:
                mode = "r"
            
            with tarfile.open(backup_file, mode) as tar:
                # Extraer todos los archivos
                tar.extractall(target_dir)
                
                # Leer metadatos
                try:
                    metadata_file = tar.extractfile("backup_metadata.json")
                    if metadata_file:
                        metadata = json.load(metadata_file)
                        self.logger.info(f"Restored backup from {metadata.get('created_at', 'unknown')}")
                except:
                    pass  # Metadatos no críticos
            
            self.logger.info(f"Backup extracted to: {target_dir}")
            
        except Exception as e:
            self.logger.error(f"Error extracting backup: {e}")
            raise
    
    def _cleanup_old_backups(self):
        """Limpiar backups antiguos"""
        try:
            with self.lock:
                # Ordenar backups por fecha
                sorted_backups = sorted(
                    self.backups.items(),
                    key=lambda x: x[1].created_at,
                    reverse=True
                )
                
                # Mantener solo los más recientes
                if len(sorted_backups) > self.max_backups:
                    backups_to_remove = sorted_backups[self.max_backups:]
                    
                    for backup_id, backup_info in backups_to_remove:
                        # Eliminar archivo
                        backup_file = Path(backup_info.file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                            self.logger.debug(f"Removed old backup file: {backup_file}")
                        
                        # Eliminar del índice
                        del self.backups[backup_id]
                    
                    self._save_backup_index()
                    self.logger.info(f"Cleaned up {len(backups_to_remove)} old backups")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def list_backups(self) -> List[BackupInfo]:
        """Listar todos los backups"""
        return list(self.backups.values())
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Obtener información de backup específico"""
        return self.backups.get(backup_id)
    
    def delete_backup(self, backup_id: str) -> bool:
        """Eliminar backup"""
        try:
            if backup_id not in self.backups:
                return False
            
            backup_info = self.backups[backup_id]
            
            # Eliminar archivo
            backup_file = Path(backup_info.file_path)
            if backup_file.exists():
                backup_file.unlink()
            
            # Eliminar del índice
            with self.lock:
                del self.backups[backup_id]
                self._save_backup_index()
            
            self.logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def get_backup_summary(self) -> Dict[str, Any]:
        """Obtener resumen de backups"""
        total_backups = len(self.backups)
        completed_backups = len([b for b in self.backups.values() if b.status == BackupStatus.COMPLETED])
        failed_backups = len([b for b in self.backups.values() if b.status == BackupStatus.FAILED])
        
        total_size = sum(b.size_bytes for b in self.backups.values())
        
        return {
            "total_backups": total_backups,
            "completed_backups": completed_backups,
            "failed_backups": failed_backups,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "backup_dir": str(self.backup_dir),
            "max_backups": self.max_backups
        }
    
    async def schedule_automatic_backups(self, interval_hours: int = 24):
        """Programar backups automáticos"""
        self.logger.info(f"Scheduling automatic backups every {interval_hours} hours")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)  # Convertir a segundos
                
                # Crear backup automático
                backup_id = await self.create_backup(
                    BackupType.FULL,
                    f"Automatic backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
                self.logger.info(f"Automatic backup created: {backup_id}")
                
            except Exception as e:
                self.logger.error(f"Error in automatic backup: {e}")

# Instancia global del backup manager
global_backup_manager = BackupManager()