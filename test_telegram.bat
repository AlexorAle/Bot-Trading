@echo off
chcp 65001 >nul
title Test Telegram
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TEST TELEGRAM                            ¦
echo +--------------------------------------------------------------+
echo.

cd /d "%~dp0"
cd backtrader_engine

echo Enviando mensaje de prueba a Telegram...
python -c "
import sys
sys.path.append('.')
from telegram_notifier import TelegramNotifier
import json

# Cargar configuracion
with open('configs/alert_config.json', 'r') as f:
    config = json.load(f)

telegram_config = config.get('telegram', {})
notifier = TelegramNotifier(telegram_config)

try:
    result = notifier.send_alert('🤖 Bot de Trading: Mensaje de prueba desde test_telegram.bat', priority='High')
    print('✅ Mensaje enviado correctamente')
    print(f'Resultado: {result}')
except Exception as e:
    print(f'❌ Error enviando mensaje: {e}')
"

echo.
echo Presiona cualquier tecla para continuar...
pause >nul
