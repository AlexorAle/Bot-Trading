# 🛡️ Backup & Disaster Recovery System

## 📋 **Resumen Ejecutivo**

El sistema de Backup & Disaster Recovery implementado proporciona protección completa de datos y recuperación automática ante fallos para el bot de trading. Incluye 5 tipos de backup, 5 tipos de disaster recovery, automatización completa y verificación de integridad.

---

## 🔄 **Tipos de Backup**

### 1. **FULL Backup**
- **Descripción**: Backup completo del sistema
- **Incluye**: Todo el proyecto, configuraciones, estado, logs, scripts
- **Frecuencia**: Diario a las 2:00 AM
- **Uso**: Recuperación completa del sistema
- **Tamaño**: ~50-100 MB (comprimido)

### 2. **STATE_ONLY Backup**
- **Descripción**: Solo estado del bot y datos de trading
- **Incluye**: `logs/bot_state.json`, posiciones, trades, PnL
- **Frecuencia**: Cada 6 horas + al iniciar bot
- **Uso**: Recuperar estado de trading sin perder historial
- **Tamaño**: ~1-5 MB

### 3. **CONFIG_ONLY Backup**
- **Descripción**: Solo archivos de configuración
- **Incluye**: `.env`, `configs/`, archivos de configuración
- **Frecuencia**: Manual
- **Uso**: Recuperar configuraciones perdidas
- **Tamaño**: ~1-2 MB

### 4. **LOGS_ONLY Backup**
- **Descripción**: Solo archivos de log
- **Incluye**: `logs/`, archivos de log del sistema
- **Frecuencia**: Manual
- **Uso**: Análisis de problemas, auditoría
- **Tamaño**: ~10-50 MB

### 5. **INCREMENTAL Backup**
- **Descripción**: Archivos modificados en las últimas 24 horas
- **Incluye**: Solo archivos cambiados
- **Frecuencia**: Manual
- **Uso**: Backup rápido de cambios recientes
- **Tamaño**: Variable

---

## 🚨 **Tipos de Disaster Recovery**

### 1. **Data Corruption** (Severidad: 7/10)
- **Detección**: Archivos críticos corruptos o vacíos
- **Archivos verificados**: `bot_state.json`, configs, `.env`
- **Plan de recuperación**:
  1. Detener procesos del bot
  2. Verificar integridad de backups
  3. Restaurar archivo de estado desde backup más reciente
  4. Restaurar archivos de configuración
  5. Validar datos restaurados
  6. Reiniciar bot con estado restaurado
- **Tiempo estimado**: 15 minutos
- **Rollback**: Sí

### 2. **System Crash** (Severidad: 8/10)
- **Detección**: Procesos del bot no están corriendo
- **Verificación**: `psutil` para detectar procesos
- **Plan de recuperación**:
  1. Evaluar daño del sistema
  2. Verificar estado de procesos
  3. Restaurar desde backup completo más reciente
  4. Recrear directorios faltantes
  5. Restaurar configuración
  6. Restaurar estado
  7. Reiniciar todos los servicios
- **Tiempo estimado**: 30 minutos
- **Rollback**: Sí

### 3. **Config Loss** (Severidad: 5/10)
- **Detección**: Archivos de configuración faltantes
- **Archivos**: `.env`, `configs/alert_config.json`, `configs/bybit_x_config.json`
- **Plan de recuperación**:
  1. Detener bot
  2. Restaurar archivos de configuración
  3. Validar configuración
  4. Reiniciar bot
- **Tiempo estimado**: 10 minutos
- **Rollback**: Sí

### 4. **State Loss** (Severidad: 6/10)
- **Detección**: Archivo `bot_state.json` faltante
- **Impacto**: Pérdida de historial de trading, PnL, posiciones
- **Plan de recuperación**:
  1. Detener bot
  2. Restaurar archivo de estado desde backup
  3. Validar integridad del estado
  4. Reiniciar bot con estado restaurado
- **Tiempo estimado**: 10 minutos
- **Rollback**: Sí

### 5. **Complete Failure** (Severidad: 10/10)
- **Detección**: Múltiples directorios y archivos críticos faltantes
- **Impacto**: Pérdida total del sistema
- **Plan de recuperación**:
  1. Evaluar daño completo
  2. Restaurar sistema completo desde backup
  3. Recrear todos los directorios
  4. Restaurar todas las configuraciones
  5. Restaurar estado y logs
  6. Validar integridad del sistema
  7. Reiniciar todos los servicios
  8. Ejecutar pruebas del sistema
- **Tiempo estimado**: 60 minutos
- **Rollback**: No

---

## 🤖 **Automatización de Backup**

### **Backup Automático en el Bot**
- **Frecuencia**: Cada 6 horas durante ejecución
- **Tipo**: FULL backup
- **Descripción**: "Automatic backup - YYYY-MM-DD HH:MM"
- **Integración**: Loop automático en `_backup_automation_loop()`

### **Backup de Inicio**
- **Momento**: Al iniciar el bot
- **Tipo**: STATE_ONLY backup
- **Descripción**: "Startup backup - YYYY-MM-DD HH:MM"
- **Propósito**: Punto de restauración antes de cambios

### **Cron Jobs Programados**
```bash
# Backup completo diario a las 2:00 AM
0 2 * * * cd /home/alex/proyectos/bot-trading && python3 scripts/backup_automation.py backup --schedule

# Backup de estado cada 6 horas
0 */6 * * * cd /home/alex/proyectos/bot-trading && python3 scripts/backup_automation.py state-backup

# Verificación de disaster recovery cada 12 horas
0 */12 * * * cd /home/alex/proyectos/bot-trading && python3 scripts/backup_automation.py disaster-check

# Limpieza de backups antiguos semanalmente (domingos a las 3:00 AM)
0 3 * * 0 cd /home/alex/proyectos/bot-trading && python3 scripts/backup_automation.py cleanup
```

---

## 🔒 **Seguridad e Integridad**

### **Verificación de Integridad**
- **Checksums MD5**: Cada backup incluye checksum para verificación
- **Validación automática**: Al restaurar, se verifica integridad
- **Detección de corrupción**: Archivos corruptos se marcan como `CORRUPTED`

### **Compresión y Almacenamiento**
- **Formato**: `tar.gz` (comprimido)
- **Metadatos**: Archivo `backup_metadata.json` incluido
- **Información**: ID, tipo, fecha, descripción, número de archivos

### **Safety Backups**
- **Antes de restaurar**: Se crea backup de seguridad automático
- **Rollback**: Posibilidad de revertir restauración
- **Descripción**: "Safety backup before restoring {backup_id}"

---

## 📊 **Integración de Datos**

### **State Persistence Integration**
- **Backup automático**: Cuando se guarda estado, se puede crear backup
- **Recuperación de estado**: Al restaurar, se restaura el estado completo
- **Continuidad**: El bot puede continuar desde el punto exacto de restauración

### **Metrics Integration**
- **Métricas de backup**: Tamaño, frecuencia, éxito/fallo
- **Alertas**: Notificaciones por fallos de backup
- **Monitoreo**: Estado de backups en dashboard

### **Error Handling Integration**
- **Circuit breakers**: Protección durante operaciones de backup
- **Retry logic**: Reintentos automáticos en caso de fallo
- **Graceful degradation**: Continuar operación aunque falle backup

---

## 🛠️ **Comandos y Herramientas**

### **Script de Automatización**
```bash
# Crear backup manual
python3 scripts/backup_automation.py backup

# Crear backup de estado
python3 scripts/backup_automation.py state-backup

# Listar todos los backups
python3 scripts/backup_automation.py list

# Restaurar backup específico
python3 scripts/backup_automation.py restore --backup-id <BACKUP_ID>

# Verificación de disaster recovery
python3 scripts/backup_automation.py disaster-check

# Limpiar backups antiguos
python3 scripts/backup_automation.py cleanup

# Configurar cron jobs
./scripts/setup_backup_cron.sh
```

### **API del BackupManager**
```python
# Crear backup programáticamente
backup_id = await backup_manager.create_backup(
    BackupType.FULL,
    "Manual backup description"
)

# Restaurar backup
success = await backup_manager.restore_backup(backup_id)

# Listar backups
backups = backup_manager.list_backups()

# Obtener información de backup
backup_info = backup_manager.get_backup_info(backup_id)

# Eliminar backup
success = backup_manager.delete_backup(backup_id)
```

---

## 📈 **Monitoreo y Alertas**

### **Métricas de Backup**
- **Tamaño total**: Espacio utilizado por backups
- **Frecuencia**: Número de backups por día/semana
- **Éxito/Fallo**: Tasa de éxito de operaciones de backup
- **Tiempo de restauración**: Duración de operaciones de restore

### **Alertas Automáticas**
- **Backup fallido**: Notificación inmediata por Telegram
- **Disaster detectado**: Alerta crítica con tipo de desastre
- **Recuperación completada**: Confirmación de recuperación exitosa
- **Espacio en disco**: Alerta si se llena el espacio de backup

### **Dashboard Integration**
- **Estado de backups**: Último backup, tamaño, estado
- **Disaster recovery status**: Estado del sistema de recuperación
- **Espacio utilizado**: Gráfico de uso de espacio de backup
- **Historial de recuperaciones**: Log de operaciones de disaster recovery

---

## 🔧 **Configuración**

### **Parámetros del BackupManager**
```python
backup_manager = BackupManager(
    backup_dir="backups",           # Directorio de backups
    max_backups=30,                 # Máximo número de backups
    compression=True,               # Compresión habilitada
    encryption_key=None             # Clave de encriptación (opcional)
)
```

### **Archivos Críticos Monitoreados**
- `logs/bot_state.json` - Estado del bot
- `configs/alert_config.json` - Configuración de alertas
- `configs/bybit_x_config.json` - Configuración de exchange
- `.env` - Variables de entorno

### **Directorios Esenciales**
- `backtrader_engine/` - Motor del bot
- `configs/` - Archivos de configuración
- `scripts/` - Scripts de automatización
- `logs/` - Archivos de log

---

## 📋 **Checklist de Implementación**

### ✅ **Backup System**
- [x] BackupManager implementado
- [x] 5 tipos de backup configurados
- [x] Compresión y checksums
- [x] Metadatos y indexación
- [x] Limpieza automática

### ✅ **Disaster Recovery**
- [x] 5 tipos de disaster detection
- [x] Planes de recuperación detallados
- [x] Validación post-recuperación
- [x] Rollback capabilities
- [x] Integración con AlertManager

### ✅ **Automatización**
- [x] Backup automático cada 6 horas
- [x] Backup de inicio
- [x] Cron jobs programados
- [x] Script de automatización CLI
- [x] Disaster recovery checks

### ✅ **Integración**
- [x] State persistence
- [x] Metrics collection
- [x] Error handling
- [x] Health monitoring
- [x] Alert notifications

---

## 🚀 **Próximos Pasos**

1. **Configurar cron jobs**: Ejecutar `./scripts/setup_backup_cron.sh`
2. **Probar backup manual**: `python3 scripts/backup_automation.py backup`
3. **Verificar disaster recovery**: `python3 scripts/backup_automation.py disaster-check`
4. **Monitorear métricas**: Verificar dashboard de métricas
5. **Configurar alertas**: Asegurar notificaciones Telegram

---

## 📞 **Soporte y Troubleshooting**

### **Logs de Backup**
- **Ubicación**: `logs/backup_automation.log`
- **Nivel**: INFO, WARNING, ERROR
- **Rotación**: Automática por tamaño

### **Problemas Comunes**
1. **Backup fallido**: Verificar espacio en disco
2. **Restore fallido**: Verificar integridad del backup
3. **Disaster recovery fallido**: Verificar backups disponibles
4. **Cron jobs no ejecutan**: Verificar permisos y configuración

### **Comandos de Diagnóstico**
```bash
# Verificar estado de backups
python3 scripts/backup_automation.py list

# Verificar disaster recovery
python3 scripts/backup_automation.py disaster-check

# Ver logs de backup
tail -f logs/backup_automation.log

# Verificar cron jobs
crontab -l
```

---

**📄 Documento generado automáticamente por el sistema de Backup & Disaster Recovery**  
**🕒 Última actualización**: $(date)  
**🤖 Sistema**: Trading Bot v2.0
