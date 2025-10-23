#!/usr/bin/env python3
"""
Backup Automation Script - Script para automatizar backups
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backtrader_engine.backup_manager import global_backup_manager, BackupType
from backtrader_engine.disaster_recovery import global_disaster_recovery

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def create_scheduled_backup():
    """Crear backup programado"""
    try:
        logger.info("Starting scheduled backup...")
        
        # Crear backup completo
        backup_id = await global_backup_manager.create_backup(
            BackupType.FULL,
            f"Scheduled backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        logger.info(f"Scheduled backup created: {backup_id}")
        
        # Obtener resumen
        summary = global_backup_manager.get_backup_summary()
        logger.info(f"Backup summary: {summary['total_backups']} total, {summary['total_size_mb']:.1f} MB")
        
        return backup_id
        
    except Exception as e:
        logger.error(f"Error creating scheduled backup: {e}")
        return None

async def create_state_backup():
    """Crear backup solo del estado"""
    try:
        logger.info("Creating state backup...")
        
        backup_id = await global_backup_manager.create_backup(
            BackupType.STATE_ONLY,
            f"State backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        logger.info(f"State backup created: {backup_id}")
        return backup_id
        
    except Exception as e:
        logger.error(f"Error creating state backup: {e}")
        return None

async def run_disaster_recovery_check():
    """Ejecutar verificación de disaster recovery"""
    try:
        logger.info("Running disaster recovery check...")
        
        success = await global_disaster_recovery.run_disaster_recovery_check()
        
        if success:
            logger.info("✅ Disaster recovery check passed")
        else:
            logger.error("❌ Disaster recovery check failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in disaster recovery check: {e}")
        return False

async def list_backups():
    """Listar backups disponibles"""
    try:
        backups = global_backup_manager.list_backups()
        
        if not backups:
            print("No backups found")
            return
        
        print(f"\n{'ID':<25} {'Type':<12} {'Status':<12} {'Size (MB)':<10} {'Created':<20}")
        print("-" * 80)
        
        for backup in sorted(backups, key=lambda x: x.created_at, reverse=True):
            size_mb = backup.size_bytes / (1024 * 1024)
            created_str = backup.created_at.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"{backup.id:<25} {backup.type.value:<12} {backup.status.value:<12} {size_mb:<10.1f} {created_str:<20}")
        
        print(f"\nTotal backups: {len(backups)}")
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")

async def restore_backup(backup_id: str):
    """Restaurar backup específico"""
    try:
        logger.info(f"Restoring backup: {backup_id}")
        
        success = await global_backup_manager.restore_backup(backup_id)
        
        if success:
            logger.info(f"✅ Backup restored successfully: {backup_id}")
        else:
            logger.error(f"❌ Failed to restore backup: {backup_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return False

async def cleanup_old_backups():
    """Limpiar backups antiguos"""
    try:
        logger.info("Cleaning up old backups...")
        
        # El backup manager ya tiene lógica de limpieza automática
        # Solo forzamos la limpieza
        global_backup_manager._cleanup_old_backups()
        
        logger.info("Old backups cleanup completed")
        
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Trading Bot Backup Automation")
    parser.add_argument("action", choices=[
        "backup", "state-backup", "restore", "list", "cleanup", "disaster-check"
    ], help="Action to perform")
    parser.add_argument("--backup-id", help="Backup ID for restore action")
    parser.add_argument("--schedule", action="store_true", help="Run as scheduled task")
    
    args = parser.parse_args()
    
    try:
        if args.action == "backup":
            backup_id = await create_scheduled_backup()
            if backup_id:
                print(f"Backup created: {backup_id}")
            else:
                print("Backup failed")
                sys.exit(1)
        
        elif args.action == "state-backup":
            backup_id = await create_state_backup()
            if backup_id:
                print(f"State backup created: {backup_id}")
            else:
                print("State backup failed")
                sys.exit(1)
        
        elif args.action == "restore":
            if not args.backup_id:
                print("Error: --backup-id required for restore action")
                sys.exit(1)
            
            success = await restore_backup(args.backup_id)
            if not success:
                sys.exit(1)
        
        elif args.action == "list":
            await list_backups()
        
        elif args.action == "cleanup":
            await cleanup_old_backups()
        
        elif args.action == "disaster-check":
            success = await run_disaster_recovery_check()
            if not success:
                sys.exit(1)
        
        # Si es una tarea programada, también ejecutar disaster recovery check
        if args.schedule:
            await run_disaster_recovery_check()
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
