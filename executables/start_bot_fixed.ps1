# PowerShell Script - Inicio del Trading Bot
# Version: 2.0 (24h Auto-Shutdown + AlwaysTrue Strategy)

param(
    [switch]$AlwaysTrue = $false,
    [int]$RuntimeHours = 24
)

$ErrorActionPreference = "SilentlyContinue"
Clear-Host

# ========== VARIABLES GLOBALES ==========
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
$BOT_DIR = Join-Path $PROJECT_DIR "backtrader_engine"
$LOG_DIR = Join-Path $BOT_DIR "logs"
$CONFIG_FILE = Join-Path $BOT_DIR "configs\bybit_x_config.json"
$MAIN_FILE = Join-Path $BOT_DIR "paper_trading_main.py"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "TRADING BOT - INICIANDO" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# ========== VALIDACIONES ==========
Write-Host "[*] Verificando archivos..." -ForegroundColor Yellow

if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
    Write-Host "[OK] Directorio de logs creado" -ForegroundColor Green
}

if (-not (Test-Path $CONFIG_FILE)) {
    Write-Host "[ERROR] Config no encontrado" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $MAIN_FILE)) {
    Write-Host "[ERROR] paper_trading_main.py no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Archivos validados" -ForegroundColor Green
Write-Host ""

# ========== INICIAR BOT ==========
Write-Host "[*] Iniciando bot..." -ForegroundColor Yellow
Write-Host "[*] Modo: Paper Trading + Testnet" -ForegroundColor Cyan
Write-Host "[*] Duración: $RuntimeHours horas" -ForegroundColor Cyan
Write-Host "[*] AlwaysTrue Strategy: $($AlwaysTrue.IsPresent)" -ForegroundColor Cyan
Write-Host ""

try {
    # Cambiar a directorio del bot
    Push-Location $BOT_DIR
    
    # Construir comando Python
    $pythonCmd = "import paper_trading_main; import asyncio; bot = paper_trading_main.PaperTradingBot(); asyncio.run(bot.start())"
    
    Write-Host "[OK] Bot iniciado. Dashboard disponible en:" -ForegroundColor Green
    Write-Host "     http://localhost:3000 (Grafana)" -ForegroundColor Cyan
    Write-Host "     http://localhost:9090 (Prometheus)" -ForegroundColor Cyan
    Write-Host "     http://localhost:8080/metrics (Métricas)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Presiona Ctrl+C para detener el bot..." -ForegroundColor Yellow
    Write-Host ""
    
    # Ejecutar bot
    python -c $pythonCmd
    
} catch {
    Write-Host "[ERROR] Error iniciando bot: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "BOT DETENIDO" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
