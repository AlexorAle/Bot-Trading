# Trading Bot Start Script - CLEAN VERSION
# PowerShell 5.1 Compatible

$ErrorActionPreference = "SilentlyContinue"
Clear-Host

# Setup
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$BOT_DIR = Join-Path $PROJECT_DIR "backtrader_engine"
$LOG_DIR = Join-Path $BOT_DIR "logs"
$MAIN_FILE = Join-Path $BOT_DIR "main.py"

# Create logs directory
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "TRADING BOT - INICIANDO" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verify Docker
Write-Host "[*] Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "[OK] Docker activo" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker no encontrado - inicia Docker Desktop" -ForegroundColor Red
    Read-Host "Presiona Enter para continuar"
    exit 1
}

# Verify files
Write-Host "[*] Verificando archivos..." -ForegroundColor Yellow
$files_ok = $true

if (-not (Test-Path $MAIN_FILE)) {
    Write-Host "[ERROR] $MAIN_FILE no encontrado" -ForegroundColor Red
    $files_ok = $false
}

if ($files_ok) {
    Write-Host "[OK] Archivos validados" -ForegroundColor Green
} else {
    Read-Host "Presiona Enter para continuar"
    exit 1
}

# Verify Docker Compose
Write-Host "[*] Verificando servicios Docker..." -ForegroundColor Yellow
$compose_file = Join-Path $PROJECT_DIR "docker-compose.yml"

if (Test-Path $compose_file) {
    try {
        Set-Location $PROJECT_DIR
        docker-compose up -d 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Host "[OK] Docker services iniciados" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] No se pudieron iniciar servicios Docker" -ForegroundColor Yellow
    }
}

# Start Bot
Write-Host ""
Write-Host "[*] Iniciando Trading Bot..." -ForegroundColor Yellow
Write-Host ""

try {
    Set-Location $BOT_DIR
    
    Write-Host "[OK] BOT ACTIVO - URLs disponibles:" -ForegroundColor Green
    Write-Host "     http://localhost:3000 (Grafana)" -ForegroundColor Cyan
    Write-Host "     http://localhost:9090 (Prometheus)" -ForegroundColor Cyan
    Write-Host "     http://localhost:8080/metrics (Metricas)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[*] Presiona Ctrl+C para detener el bot" -ForegroundColor Yellow
    Write-Host ""
    
    # Start bot
    python main.py
    
} catch {
    Write-Host "[ERROR] Error: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Presiona Enter para continuar"
    exit 1
} finally {
    Set-Location $PROJECT_DIR
}

Write-Host ""
Write-Host "[OK] Bot detenido" -ForegroundColor Green
