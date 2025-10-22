# PowerShell script para verificar el estado del Trading Bot
# Autor: Trading Bot System
# Fecha: 2025-10-17

# Configuración de colores y encoding
$Host.UI.RawUI.WindowTitle = "Trading Bot - Verificando Estado"
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
Clear-Host

# Variables
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$BOT_DIR = Join-Path $PROJECT_DIR "backtrader_engine"
$LOG_FILE = Join-Path $BOT_DIR "logs\system_init.log"
$PID_MANAGER = Join-Path $PROJECT_DIR "executables\bot_pid_manager.py"

# Función para mostrar estado
function Show-Status {
    param($Item, $Status, $Details = "")
    if ($Status -eq "OK") {
        Write-Host "$Item`: ✓ OK" -ForegroundColor Green
    } elseif ($Status -eq "ERROR") {
        Write-Host "$Item`: ✗ ERROR" -ForegroundColor Red
    } elseif ($Status -eq "WARNING") {
        Write-Host "$Item`: ⚠ WARNING" -ForegroundColor Yellow
    } else {
        Write-Host "$Item`: $Status" -ForegroundColor White
    }
    if ($Details) {
        Write-Host "  $Details" -ForegroundColor Gray
    }
}

# Función para verificar servicio
function Test-Service {
    param($Name, $Url, $Icon = "🔌")
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Show-Status "$Icon $Name" "OK"
            return $true
        } else {
            Show-Status "$Icon $Name" "ERROR" "Status: $($response.StatusCode)"
            return $false
        }
    } catch {
        Show-Status "$Icon $Name" "ERROR" "No disponible"
        return $false
    }
}

# Header
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "|      TRADING BOT - VERIFICANDO ESTADO    |" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar estado del bot usando PID Manager
Write-Host "🤖 ESTADO DEL BOT:" -ForegroundColor Yellow
Write-Host ""

try {
    $statusResult = python $PID_MANAGER status 2>$null
    if ($statusResult) {
        # Parsear JSON del resultado
        $statusJson = $statusResult | ConvertFrom-Json
        
        if ($statusJson.is_running) {
            Show-Status "Bot Status" "OK" "Ejecutándose (PID: $($statusJson.pid))"
            Show-Status "Total Procesos" "OK" "$($statusJson.total_processes) proceso(s)"
            
            if ($statusJson.processes -and $statusJson.processes.Count -gt 0) {
                Write-Host ""
                Write-Host "📋 PROCESOS ACTIVOS:" -ForegroundColor Yellow
                foreach ($proc in $statusJson.processes) {
                    Write-Host "  PID: $($proc.pid)" -ForegroundColor Green
                    Write-Host "  CMD: $($proc.cmdline)" -ForegroundColor Gray
                    Write-Host ""
                }
            }
        } else {
            Show-Status "Bot Status" "ERROR" "No está ejecutándose"
            Show-Status "PID" "ERROR" "N/A"
        }
        
        $timestamp = [DateTime]::Parse($statusJson.timestamp)
        Show-Status "Última Verificación" "OK" $timestamp.ToString("yyyy-MM-dd HH:mm:ss")
    } else {
        Show-Status "Bot Status" "ERROR" "No se pudo obtener estado"
    }
} catch {
    Show-Status "Bot Status" "ERROR" "Error al verificar: $($_.Exception.Message)"
}

Write-Host ""

# Verificar servicios
Write-Host "🔧 SERVICIOS DEL SISTEMA:" -ForegroundColor Yellow
Write-Host ""

$services = @{
    "Prometheus" = "http://localhost:9090"
    "Grafana" = "http://localhost:3000"
    "Metrics API" = "http://localhost:8080/metrics"
}

$servicesOK = 0
$totalServices = $services.Count

foreach ($service in $services.GetEnumerator()) {
    if (Test-Service $service.Key $service.Value) {
        $servicesOK++
    }
}

Write-Host ""

# Verificar métricas si el bot está ejecutándose
if ($statusJson -and $statusJson.is_running) {
    Write-Host "📊 MÉTRICAS DEL BOT:" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        $metricsResponse = Invoke-WebRequest -Uri "http://localhost:8080/metrics" -TimeoutSec 5 -UseBasicParsing
        if ($metricsResponse.StatusCode -eq 200) {
            $metrics = @{}
            foreach ($line in $metricsResponse.Content.Split("`n")) {
                if ($line.StartsWith("paper_") -and -not $line.StartsWith("#")) {
                    $parts = $line.Split()
                    if ($parts.Length -ge 2) {
                        $metrics[$parts[0]] = $parts[1]
                    }
                }
            }
            
            if ($metrics.Count -gt 0) {
                Show-Status "Métricas Disponibles" "OK" "$($metrics.Count) métricas"
                
                # Mostrar métricas importantes
                $importantMetrics = @{
                    "paper_signals_generated_total" = "Señales Generadas"
                    "paper_signals_executed_total" = "Señales Ejecutadas"
                    "paper_signals_rejected_total" = "Señales Rechazadas"
                    "paper_portfolio_value" = "Valor Portfolio"
                    "paper_pnl_total" = "P&L Total"
                }
                
                foreach ($metric in $importantMetrics.GetEnumerator()) {
                    if ($metrics.ContainsKey($metric.Key)) {
                        Show-Status $metric.Value "OK" $metrics[$metric.Key]
                    }
                }
            } else {
                Show-Status "Métricas" "WARNING" "No hay métricas disponibles"
            }
        } else {
            Show-Status "Métricas" "ERROR" "No se pudo conectar al endpoint"
        }
    } catch {
        Show-Status "Métricas" "ERROR" "Error al obtener métricas"
    }
    
    Write-Host ""
}

# Verificar logs
Write-Host "📜 LOGS RECIENTES:" -ForegroundColor Yellow
Write-Host ""

if (Test-Path $LOG_FILE) {
    try {
        $logLines = Get-Content $LOG_FILE -Tail 5 -ErrorAction SilentlyContinue
        if ($logLines) {
            Show-Status "Archivo de Log" "OK" "Últimas 5 líneas disponibles"
            Write-Host ""
            foreach ($line in $logLines) {
                Write-Host "  $line" -ForegroundColor Gray
            }
        } else {
            Show-Status "Archivo de Log" "WARNING" "Archivo vacío"
        }
    } catch {
        Show-Status "Archivo de Log" "ERROR" "No se pudo leer"
    }
} else {
    Show-Status "Archivo de Log" "ERROR" "No existe"
}

Write-Host ""

# Resumen final
Write-Host "📋 RESUMEN:" -ForegroundColor Yellow
Write-Host ""

$botStatus = if ($statusJson -and $statusJson.is_running) { "ACTIVO" } else { "INACTIVO" }
$servicesStatus = "$servicesOK/$totalServices servicios OK"

Show-Status "Bot" $botStatus
Show-Status "Servicios" $servicesStatus

if ($statusJson -and $statusJson.is_running) {
    Write-Host ""
    Write-Host "✅ El bot está funcionando correctamente" -ForegroundColor Green
    Write-Host "🔗 URLs disponibles:" -ForegroundColor Cyan
    Write-Host "   Grafana: http://localhost:3000" -ForegroundColor White
    Write-Host "   Prometheus: http://localhost:9090" -ForegroundColor White
    Write-Host "   Métricas: http://localhost:8080/metrics" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ El bot no está ejecutándose" -ForegroundColor Red
    Write-Host "🚀 Para iniciar: executables\start_bot.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "|         VERIFICACIÓN COMPLETADA           |" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presiona Enter para continuar"
