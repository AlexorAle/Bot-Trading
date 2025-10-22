@echo off
chcp 65001 >nul
title Test Telegram Simple
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    TEST TELEGRAM SIMPLE                     ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Enviando mensaje de prueba a Telegram...
echo.

cd backtrader_engine

echo Creando script temporal de Python...
echo import sys > temp_telegram_test.py
echo sys.path.append('.') >> temp_telegram_test.py
echo from telegram_notifier import TelegramNotifier >> temp_telegram_test.py
echo import json >> temp_telegram_test.py
echo. >> temp_telegram_test.py
echo try: >> temp_telegram_test.py
echo     with open('configs/alert_config.json', 'r') as f: >> temp_telegram_test.py
echo         config = json.load(f) >> temp_telegram_test.py
echo     telegram_config = config.get('telegram', {}) >> temp_telegram_test.py
echo     notifier = TelegramNotifier(telegram_config) >> temp_telegram_test.py
echo     result = notifier.send_message('🤖 Bot de Trading: Mensaje de prueba desde test_telegram_simple.bat') >> temp_telegram_test.py
echo     print('OK: Mensaje enviado correctamente') >> temp_telegram_test.py
echo     print(f'Resultado: {result}') >> temp_telegram_test.py
echo except Exception as e: >> temp_telegram_test.py
echo     print(f'ERROR: Error enviando mensaje: {e}') >> temp_telegram_test.py

echo Ejecutando script de Python...
python temp_telegram_test.py

echo.
echo Limpiando archivo temporal...
del temp_telegram_test.py

echo.
echo +--------------------------------------------------------------+
echo ¦                    TEST COMPLETADO                           ¦
echo +--------------------------------------------------------------+
echo.
echo Revisa tu Telegram para ver si llego el mensaje
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
