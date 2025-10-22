# PowerShell script para detener el Trading Bot
# Autor: Trading Bot System
# Fecha: 2025-10-17

# Configuración de colores y encoding
$Host.UI.RawUI.WindowTitle = "Trading Bot - Deteniendo Sistema"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
Clear-Host

# Variables
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$BOT_DIR = Join-Path $PROJECT_DIR "backtrader_engine"
$LOG_FILE = Join-Path $BOT_DIR "logs\system_init.log"
$PID_MANAGER = Join-Path $PROJECT_DIR "executables\bot_pid_manager.py"
$COMPOSE_FILE = Join-Path $PROJECT_DIR "docker-compose.yml"

# Función para logging
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $LOG_FILE -Value $logMessage
}

# Función para mostrar estado
function Show-Status {
    param($Item, $Status)
    if ($Status -eq "OK") {
        Write-Host "$Item`: ✓ OK" -ForegroundColor Green
    } else {
        Write-Host "$Item`: ✗ ERROR" -ForegroundColor Red
    }
    Write-Log "$Item`: $Status"
}

# Header
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "|         TRADING BOT - DETENIENDO         |" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Log "=== DETENIENDO BOT ==="

# Verificar estado actual del bot
Write-Host "Verificando estado actual del bot..."
$statusResult = python $PID_MANAGER status 2>$null
if ($statusResult -match '"is_running":\s*false') {
    Write-Host "El bot ya está detenido." -ForegroundColor Yellow
    goto :CLEANUP
}

# Enviar alerta de detención a Telegram
Write-Host "Enviando alerta de detención a Telegram..."
Set-Location $BOT_DIR
try {
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('🛑 Bot de Trading deteniendo...')" 2>$null
    Show-Status "Telegram" "OK"
} catch {
    Show-Status "Telegram" "ERROR"
}

# Intentar detención graceful
Write-Host "Intentando detención graceful..."
try {
    $result = python $PID_MANAGER stop
    if ($LASTEXITCODE -eq 0) {
        Show-Status "Detención Graceful" "OK"
        goto :VERIFY_STOP
    } else {
        Show-Status "Detención Graceful" "ERROR"
        Write-Host "Intentando detención forzada..."
    }
} catch {
    Show-Status "Detención Graceful" "ERROR"
    Write-Host "Intentando detención forzada..."
}

# Intentar detención forzada
Write-Host "Intentando detención forzada..."
try {
    $result = python $PID_MANAGER force-stop
    if ($LASTEXITCODE -eq 0) {
        Show-Status "Detención Forzada" "OK"
        goto :VERIFY_STOP
    } else {
        Show-Status "Detención Forzada" "ERROR"
        Write-Host "Intentando métodos manuales..."
        goto :MANUAL_STOP
    }
} catch {
    Show-Status "Detención Forzada" "ERROR"
    Write-Host "Intentando métodos manuales..."
    goto :MANUAL_STOP
}

:VERIFY_STOP
Write-Host "Verificando que el bot se haya detenido..."
Start-Sleep -Seconds 3

$statusResult = python $PID_MANAGER status 2>$null
if ($statusResult -match '"is_running":\s*false') {
    Show-Status "Verificación" "OK"
    goto :SUCCESS
} else {
    Show-Status "Verificación" "ERROR"
    Write-Host "El bot aún está ejecutándose. Intentando métodos manuales..."
    goto :MANUAL_STOP
}

:MANUAL_STOP
Write-Host "=== METODOS MANUALES DE DETENCION ==="

# Método 1: Buscar por nombre de proceso
Write-Host "Método 1: Buscando procesos por nombre..."
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
foreach ($proc in $pythonProcesses) {
    try {
        $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdline -and $cmdline.Contains("paper_trading_main.py")) {
            Write-Host "Terminando proceso $($proc.Id)..."
            Stop-Process -Id $proc.Id -Force
            if ($?) {
                Show-Status "Proceso $($proc.Id)" "TERMINADO"
            } else {
                Show-Status "Proceso $($proc.Id)" "ERROR"
            }
        }
    } catch {
        # Ignorar errores de acceso
    }
}

# Método 2: Terminar por puerto 8080
Write-Host "Método 2: Buscando proceso por puerto 8080..."
try {
    $port8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
    if ($port8080) {
        $pid = $port8080.OwningProcess
        Write-Host "Terminando proceso en puerto 8080: $pid..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        if ($?) {
            Show-Status "Puerto 8080" "LIBERADO"
        } else {
            Show-Status "Puerto 8080" "ERROR"
        }
    }
} catch {
    Show-Status "Puerto 8080" "ERROR"
}

# Verificar detención final
Write-Host "Verificando detención final..."
Start-Sleep -Seconds 5

$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Show-Status "Verificación Final" "ERROR"
    Write-Host "Aún hay procesos Python ejecutándose. Revisa manualmente." -ForegroundColor Red
    goto :FAILURE
} else {
    Show-Status "Verificación Final" "OK"
    goto :SUCCESS
}

:SUCCESS
Write-Host "Enviando confirmación a Telegram..."
Set-Location $BOT_DIR
try {
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('✅ Bot de Trading detenido correctamente')" 2>$null
} catch {
    # Ignorar errores de Telegram
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "|         BOT DETENIDO CORRECTAMENTE         |" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Estado: Bot detenido" -ForegroundColor Yellow
Write-Host "Logs: $LOG_FILE" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para reiniciar: executables\start_bot.ps1" -ForegroundColor Cyan
goto :CLEANUP

:FAILURE
Write-Host "Enviando error a Telegram..."
Set-Location $BOT_DIR
try {
    python -c "import sys, json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; config = json.load(open('configs/alert_config.json')); notifier = TelegramNotifier(config.get('telegram', {})); notifier.send_message('❌ Error deteniendo Bot de Trading')" 2>$null
} catch {
    # Ignorar errores de Telegram
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Red
Write-Host "|         ERROR DETENIENDO BOT               |" -ForegroundColor Red
Write-Host "=============================================" -ForegroundColor Red
Write-Host ""
Write-Host "El bot no se pudo detener completamente." -ForegroundColor Red
Write-Host "Revisa los logs en: $LOG_FILE" -ForegroundColor Yellow

:CLEANUP
Write-Host ""
Write-Host "Limpieza completada." -ForegroundColor Green
Write-Host ""
Read-Host "Presiona Enter para continuar"
