chcp 65001 > $null
Write-Host "`n🛑 Deteniendo Trading Bot...`n" -ForegroundColor Cyan

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$botDir = Join-Path $projectDir "..\backtrader_engine"
$configAlert = Join-Path $botDir "configs\alert_config.json"
$logFile = Join-Path $botDir "logs\system_init.log"
$composeFile = Join-Path $projectDir "..\docker-compose.yml"

function Show-Status($label, $ok) {
    if ($ok) {
        Write-Host "$label:`t✓ OK" -ForegroundColor Green
    } else {
        Write-Host "$label:`t✗ ERROR" -ForegroundColor Red
    }
}

cd $botDir
python -c "import sys,json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; c=json.load(open('$configAlert')); TelegramNotifier(c.get('telegram',{})).send_message('Deteniendo bot...')" >> $logFile 2>&1
Show-Status "Telegram Stop" $true

Get-Process python | Where-Object { $_.Path -like '*paper_trading_main.py*' } | Stop-Process -Force
Show-Status "Bot detenido" $true

cd $projectDir
docker-compose -f $composeFile down >> $logFile 2>&1
Show-Status "Servicios Docker" $true
