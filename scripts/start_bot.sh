#!/bin/bash
# start_bot.sh - Script para iniciar el Trading Bot de forma robusta

set -e

PROJECT_DIR="/home/alex/proyectos/bot-trading"
BOT_DIR="$PROJECT_DIR/backtrader_engine"
LOG_DIR="$BOT_DIR/logs"
PID_FILE="$LOG_DIR/bot.pid"
LOG_FILE="$LOG_DIR/paper_trading.log"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Trading Bot - START Script${NC}"
echo -e "${GREEN}====================================${NC}"

# Crear directorio de logs
mkdir -p "$LOG_DIR"

# Verificar si ya está corriendo
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Bot ya está corriendo (PID: $OLD_PID)${NC}"
        exit 1
    else
        echo -e "${YELLOW}Limpiando PID antiguo...${NC}"
        rm -f "$PID_FILE"
    fi
fi

# Activar entorno virtual
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo -e "${GREEN}Activando entorno virtual...${NC}"
    source "$PROJECT_DIR/venv/bin/activate"
    PYTHON_CMD="$PROJECT_DIR/venv/bin/python"
else
    echo -e "${YELLOW}No se encontró venv, usando python3 del sistema${NC}"
    PYTHON_CMD="python3"
fi

# Verificar script
BOT_SCRIPT="$BOT_DIR/paper_trading_main.py"
if [ ! -f "$BOT_SCRIPT" ]; then
    echo -e "${RED}✗ Script no encontrado: $BOT_SCRIPT${NC}"
    exit 1
fi

# Iniciar bot en background
echo -e "${GREEN}Iniciando Trading Bot...${NC}"
cd "$BOT_DIR"

nohup $PYTHON_CMD "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
BOT_PID=$!

# Guardar PID
echo $BOT_PID > "$PID_FILE"

# Esperar 3 segundos y verificar
sleep 3

if ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Bot iniciado correctamente (PID: $BOT_PID)${NC}"
    echo -e "${GREEN}✓ Logs: $LOG_FILE${NC}"
else
    echo -e "${RED}✗ Bot falló al iniciar. Revise logs: $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Para detener: ./scripts/stop_bot.sh${NC}"
echo -e "${GREEN}Para ver logs: tail -f $LOG_FILE${NC}"
echo -e "${GREEN}====================================${NC}"

