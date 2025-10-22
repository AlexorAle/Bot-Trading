#!/bin/bash
# status_bot.sh - Script para verificar el estado del Trading Bot

PROJECT_DIR="/home/alex/proyectos/bot-trading"
LOG_DIR="$PROJECT_DIR/backtrader_engine/logs"
PID_FILE="$LOG_DIR/bot.pid"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}Trading Bot - STATUS${NC}"
echo -e "${BLUE}====================================${NC}"

# Buscar proceso
BOT_PID=""
if [ -f "$PID_FILE" ]; then
    BOT_PID=$(cat "$PID_FILE")
fi

# Verificar si está corriendo
if [ -n "$BOT_PID" ] && ps -p $BOT_PID > /dev/null 2>&1; then
    PROC_INFO=$(ps -p $BOT_PID -o pid,etime,pcpu,pmem,cmd --no-headers)
    echo -e "${GREEN}✓ Bot está CORRIENDO${NC}"
    echo ""
    echo -e "${BLUE}PID:${NC} $BOT_PID"
    echo -e "${BLUE}Proceso:${NC}"
    echo "$PROC_INFO"
    echo ""
    
    # Mostrar últimas líneas del log
    LOG_FILE="$LOG_DIR/paper_trading.log"
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}Últimas 5 líneas del log:${NC}"
        tail -5 "$LOG_FILE"
    fi
else
    echo -e "${RED}✗ Bot NO está corriendo${NC}"
    
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Limpiando PID file obsoleto...${NC}"
        rm -f "$PID_FILE"
    fi
fi

echo -e "${BLUE}====================================${NC}"

