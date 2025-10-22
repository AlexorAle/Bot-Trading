@echo off
chcp 65001 >nul
title Test Telegram Ultra Simple
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TEST TELEGRAM ULTRA SIMPLE               ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Enviando mensaje de prueba a Telegram...
echo.

cd backtrader_engine

echo Ejecutando test directo...
python -c "import sys; sys.path.append('.'); from telegram_notifier import TelegramNotifier; import json; config = json.load(open('configs/alert_config.json', 'r')); telegram_config = config.get('telegram', {}); notifier = TelegramNotifier(telegram_config); result = notifier.send_message('🤖 Bot de Trading: Mensaje de prueba desde test_telegram_ultra_simple.bat'); print('OK: Mensaje enviado correctamente' if result else 'ERROR: No se pudo enviar el mensaje'); print(f'Resultado: {result}')"

echo.
echo +--------------------------------------------------------------+
echo ¦                    TEST COMPLETADO                           ¦
echo +--------------------------------------------------------------+
echo.
echo Revisa tu Telegram para ver si llego el mensaje
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
