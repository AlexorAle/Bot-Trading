chcp 65001 > $null
Write-Host "`n🚀 Iniciando Trading Bot...`n" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$botDir = Join-Path $projectDir "..\backtrader_engine"
$configAlert = Join-Path $botDir "configs\alert_config.json"
$configBybit = Join-Path $botDir "configs\bybit_x_config.json"
$logFile = Join-Path $botDir "logs\system_init.log"
$composeFile = Join-Path $projectDir "..\docker-compose.yml"

function Show-Status($label, $ok) {
    if ($ok) {
        Write-Host "$label:`t✓ OK" -ForegroundColor Green
    } else {
        Write-Host "$label:`t✗ ERROR" -ForegroundColor Red
    }
}

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Show-Status "Python" $false
    exit 1
} else {
    Show-Status "Python" $true
}

if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Show-Status "Docker" $false
    exit 1
} else {
    Show-Status "Docker" $true
}

$servicesStarted = $false
if (-not (Get-NetTCPConnection -LocalPort 9090 -ErrorAction SilentlyContinue)) {
    docker-compose -f $composeFile up -d prometheus >> $logFile 2>&1
    $servicesStarted = $true
}
if (-not (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue)) {
    docker-compose -f $composeFile up -d grafana >> $logFile 2>&1
    $servicesStarted = $true
}
if ($servicesStarted) { Start-Sleep -Seconds 10 }
Show-Status "Servicios Docker" $true

if (!(Test-Path $configBybit) -or !(Test-Path $configAlert)) {
    Show-Status "Configs" $false
    exit 1
} else {
    Show-Status "Configs" $true
}

cd $botDir
python -c "import sys,json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; c=json.load(open('$configAlert')); TelegramNotifier(c.get('telegram',{})).send_message('Iniciando bot...')" >> $logFile 2>&1
Show-Status "Telegram Inicial" $true

python paper_trading_main.py --config $configBybit >> $logFile 2>&1
if ($LASTEXITCODE -eq 0) {
    Show-Status "Bot lanzado" $true
} else {
    Show-Status "Bot lanzado" $false
}
