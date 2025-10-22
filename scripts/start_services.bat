@echo off
chcp 65001 >nul
title Trading Bot - Iniciando Servicios
color 0A

echo.
echo +--------------------------------------------------------------+
echo ¦                    DOCKER SERVICES                           ¦
echo ¦                    Iniciando Servicios                      ¦
echo +--------------------------------------------------------------+
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\.."

echo Verificando Docker Desktop...
docker version >nul 2>&1
if %errorlevel% == 0 (
    echo OK: Docker Desktop ejecutandose
) else (
    echo ERROR: Docker Desktop no esta ejecutandose
    echo Inicia Docker Desktop manualmente
    echo.
    pause
    exit /b 1
)

echo.
echo Iniciando servicios de monitoreo...
echo.

echo Iniciando Prometheus...
docker-compose up -d prometheus
if %errorlevel% == 0 (
    echo OK: Prometheus iniciado
) else (
    echo ERROR: Error iniciando Prometheus
    echo Verifica que docker-compose.yml existe
)

echo.
echo Iniciando Grafana...
docker-compose up -d grafana
if %errorlevel% == 0 (
    echo OK: Grafana iniciado
) else (
    echo ERROR: Error iniciando Grafana
    echo Verifica que docker-compose.yml existe
)

echo.
echo Esperando que los servicios esten listos...
timeout /t 10 /nobreak >nul

echo.
echo Verificando estado de los servicios...
echo.

echo Verificando Prometheus (puerto 9090)...
netstat -an | findstr ":9090" >nul
if %errorlevel% == 0 (
    echo OK: Prometheus ejecutandose
) else (
    echo ERROR: Prometheus no esta ejecutandose
)

echo.
echo Verificando Grafana (puerto 3000)...
netstat -an | findstr ":3000" >nul
if %errorlevel% == 0 (
    echo OK: Grafana ejecutandose
) else (
    echo ERROR: Grafana no esta ejecutandose
)

echo.
echo +--------------------------------------------------------------+
echo ¦                    SERVICIOS INICIADOS                      ¦
echo +--------------------------------------------------------------+
echo.
echo Grafana: http://localhost:3000 (admin/admin)
echo Prometheus: http://localhost:9090
echo.
echo Ahora puedes ejecutar: scripts\start_bot.bat
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
