#!/bin/bash

# Setup Backup Cron Jobs
# Este script configura los cron jobs para backups automáticos

SCRIPT_DIR="/home/alex/proyectos/bot-trading"
BACKUP_SCRIPT="$SCRIPT_DIR/scripts/backup_automation.py"
LOG_FILE="$SCRIPT_DIR/logs/backup_cron.log"

echo "Setting up backup cron jobs..."

# Crear directorio de logs si no existe
mkdir -p "$SCRIPT_DIR/logs"

# Crear archivo de cron temporal
CRON_FILE="/tmp/trading_bot_cron"

cat > "$CRON_FILE" << EOF
# Trading Bot Backup Automation
# Backup completo diario a las 2:00 AM
0 2 * * * cd $SCRIPT_DIR && python3 $BACKUP_SCRIPT backup --schedule >> $LOG_FILE 2>&1

# Backup de estado cada 6 horas
0 */6 * * * cd $SCRIPT_DIR && python3 $BACKUP_SCRIPT state-backup >> $LOG_FILE 2>&1

# Verificación de disaster recovery cada 12 horas
0 */12 * * * cd $SCRIPT_DIR && python3 $BACKUP_SCRIPT disaster-check >> $LOG_FILE 2>&1

# Limpieza de backups antiguos semanalmente (domingos a las 3:00 AM)
0 3 * * 0 cd $SCRIPT_DIR && python3 $BACKUP_SCRIPT cleanup >> $LOG_FILE 2>&1
EOF

# Instalar cron jobs
echo "Installing cron jobs..."
crontab "$CRON_FILE"

# Verificar instalación
echo "Current cron jobs:"
crontab -l | grep -E "(backup|disaster)"

# Limpiar archivo temporal
rm "$CRON_FILE"

echo "Backup cron jobs installed successfully!"
echo "Logs will be written to: $LOG_FILE"
echo ""
echo "Cron schedule:"
echo "- Full backup: Daily at 2:00 AM"
echo "- State backup: Every 6 hours"
echo "- Disaster recovery check: Every 12 hours"
echo "- Cleanup: Weekly on Sundays at 3:00 AM"
