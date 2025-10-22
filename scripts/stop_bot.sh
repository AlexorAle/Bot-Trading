#!/bin/bash
# stop_bot.sh - Script para detener el Trading Bot

PROJECT_DIR="/home/alex/proyectos/bot-trading"
LOG_DIR="$PROJECT_DIR/backtrader_engine/logs"
PID_FILE="$LOG_DIR/bot.pid"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}====================================${NC}"
echo -e "${YELLOW}Trading Bot - STOP Script${NC}"
echo -e "${YELLOW}====================================${NC}"

# Verificar si existe archivo PID
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}No se encontró archivo PID${NC}"
    echo -e "${YELLOW}Buscando proceso manualmente...${NC}"
    
    # Buscar proceso por nombre
    BOT_PID=$(ps aux | grep "paper_trading_main.py" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -z "$BOT_PID" ]; then
        echo -e "${RED}✗ Bot no está corriendo${NC}"
        exit 1
    fi
else
    BOT_PID=$(cat "$PID_FILE")
fi

# Verificar si el proceso existe
if ! ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${RED}✗ Proceso no encontrado (PID: $BOT_PID)${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

# Detener proceso
echo -e "${YELLOW}Deteniendo bot (PID: $BOT_PID)...${NC}"
kill -TERM $BOT_PID

# Esperar hasta 10 segundos
for i in {1..10}; do
    if ! ps -p $BOT_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Bot detenido correctamente${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Si no se detuvo, forzar
echo -e "${YELLOW}Forzando detención...${NC}"
kill -9 $BOT_PID 2>/dev/null

sleep 1

if ! ps -p $BOT_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Bot detenido (forzado)${NC}"
    rm -f "$PID_FILE"
else
    echo -e "${RED}✗ No se pudo detener el bot${NC}"
    exit 1
fi

