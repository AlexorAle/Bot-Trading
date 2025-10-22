
chcp 65001 > $null
Clear-Host
Write-Host "🧠 Trading Bot - Menú de Control Principal`n" -ForegroundColor Cyan

function Show-Menu {
    Write-Host "=============================="
    Write-Host " [1] 🚀 Iniciar Trading Bot"
    Write-Host " [2] 🔍 Verificar Estado del Bot"
    Write-Host " [3] 🛑 Detener Trading Bot"
    Write-Host " [4] 📤 Enviar Mensaje de Prueba (Telegram)"
    Write-Host " [5] ❌ Salir"
    Write-Host "=============================="
}

do {
    Show-Menu
    $choice = Read-Host "Selecciona una opción [1-5]"

    switch ($choice) {
        "1" {
            Write-Host "`nEjecutando start_bot.ps1..." -ForegroundColor Yellow
            .\start_bot.ps1
        }
        "2" {
            Write-Host "`nVerificando estado con check_bot_status.ps1..." -ForegroundColor Yellow
            .\check_bot_status.ps1
        }
        "3" {
            Write-Host "`nDeteniendo con stop_bot.ps1..." -ForegroundColor Yellow
            .\stop_bot.ps1
        }
        "4" {
            $configPath = "..\backtrader_engine\configs\alert_config.json"
            Write-Host "`nEnviando mensaje de prueba a Telegram..." -ForegroundColor Yellow
            python -c "import sys,json; sys.path.append('.'); from telegram_notifier import TelegramNotifier; c=json.load(open('$configPath')); TelegramNotifier(c.get('telegram', {})).send_message('🔔 Test de alerta desde menú.ps1')" 
        }
        "5" {
            Write-Host "`nSaliendo..." -ForegroundColor Red
            break
        }
        Default {
            Write-Host "Opción inválida. Intenta nuevamente." -ForegroundColor Red
        }
    }

    if ($choice -ne "5") {
        Write-Host "`nPresiona ENTER para continuar..."
        [void][System.Console]::ReadLine()
        Clear-Host
    }
} while ($choice -ne "5")
