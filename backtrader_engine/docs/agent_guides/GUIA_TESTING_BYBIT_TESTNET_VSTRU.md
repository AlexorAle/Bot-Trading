#  Guía de Testing: Bot con Estrategia VSTRU en Bybit Testnet

##  **OBJETIVO**
Validar que el bot puede:
1.  Iniciar correctamente usando scripts existentes
2.  Generar señales cada 15 minutos con estrategia VSTRU
3.  Crear órdenes REALES en Bybit Testnet
4.  Procesar señales y ejecutar trades

---

##  **PASO 1: Verificar Scripts Existentes**

### **Ubicación de Scripts**
`
 C:\Mis_Proyectos\BOT Trading\backtrader_engine\executables\
 start_bot.ps1           Script para iniciar bot
 stop_bot.ps1            Script para detener bot
 check_bot_status.ps1    Script para verificar estado
 start_bot.bat           Script alternativo (Windows)
`

### **Comando para Iniciar**
`powershell
# Navegar al directorio
cd "C:\Mis_Proyectos\BOT Trading\backtrader_engine\executables"

# Ejecutar script de inicio
.\start_bot.ps1
`

### **Verificar que Funciona**
-  Bot debe mostrar "Bot iniciado correctamente"
-  Telegram debe recibir mensaje de inicio
-  Prometheus debe mostrar métricas en http://localhost:8000/metrics
-  Grafana debe mostrar bot como "ONLINE"

---

##  **PASO 2: Verificar Estrategia VSTRU**

### **¿Existe la Estrategia VSTRU?**
**VERIFICAR PRIMERO** si la estrategia VSTRU está implementada:

`ash
# Buscar archivos relacionados con VSTRU
grep -r "VSTRU" backtrader_engine/
grep -r "15.*minute" backtrader_engine/
grep -r "900.*second" backtrader_engine/  # 15 min = 900 seg
`

### **Si NO existe VSTRU:**
**CREAR estrategia VSTRU** con estas características:
-  **Frecuencia**: Cada 15 minutos (900 segundos)
-  **Símbolos**: ETHUSDT, BTCUSDT, SOLUSDT
-  **Lógica**: Simple (ej: RSI + EMA crossover)
-  **Señales**: BUY/SELL alternados cada 15 min

### **Si SÍ existe VSTRU:**
**VERIFICAR** que esté en:
- configs/strategies_config_optimized.json
- signal_engine.py (método implementado)
- Configuración activa

---

##  **PASO 3: Configurar Estrategia VSTRU**

### **Archivo de Configuración**
`json
{
  "name": "VSTRUStrategy",
  "enabled": true,
  "symbols": ["ETHUSDT", "BTCUSDT", "SOLUSDT"],
  "parameters": {
    "signal_interval_seconds": 900,  // 15 minutos
    "rsi_period": 14,
    "ema_period": 20,
    "position_size": 0.05,
    "take_profit": 0.02,
    "stop_loss": 0.01
  },
  "risk_limits": {
    "max_position_size": 0.05,
    "max_daily_trades": 12  // 12 trades por día (cada 15 min)
  },
  "weight": 0.3,
  "description": "Estrategia VSTRU - Señales cada 15 minutos"
}
`

### **Implementación en signal_engine.py**
`python
def _vstru_signal(self, symbol, price, timestamp, indicators, params):
    """
    Estrategia VSTRU: Señales cada 15 minutos
    """
    current_time = int(timestamp)
    interval = params.get('signal_interval_seconds', 900)  # 15 min
    
    # Verificar si es tiempo de generar señal
    if current_time % interval != 0:
        return None
    
    # Lógica simple: RSI + EMA
    rsi = indicators.get('rsi', 50)
    ema = indicators.get('ema_20', price)
    
    if rsi > 60 and price > ema:
        return TradingSignal(
            symbol=symbol,
            signal_type='BUY',
            confidence=0.75,
            price=price,
            strategy='VSTRUStrategy',
            timestamp=timestamp,
            indicators=indicators
        )
    elif rsi < 40 and price < ema:
        return TradingSignal(
            symbol=symbol,
            signal_type='SELL',
            confidence=0.75,
            price=price,
            strategy='VSTRUStrategy',
            timestamp=timestamp,
            indicators=indicators
        )
    
    return None
`

---

##  **PASO 4: Conectar con Bybit Testnet**

### **Configuración de Bybit Testnet**
`json
{
  "exchange": {
    "name": "bybit",
    "testnet": true,
    "api_key": "TU_API_KEY_TESTNET",
    "api_secret": "TU_API_SECRET_TESTNET",
    "sandbox": true
  }
}
`

### **Verificar Conexión**
-  Bot debe conectar a Bybit Testnet
-  WebSocket debe recibir datos en tiempo real
-  API debe responder a requests

---

##  **PASO 5: Monitorear Órdenes en Bybit**

### **Dashboard de Bybit Testnet**
1. **Acceder**: https://testnet.bybit.com/
2. **Login**: Con credenciales de testnet
3. **Ir a**: Trading  Spot Trading
4. **Monitorear**: Órdenes activas y historial

### **Verificar Órdenes Creadas**
-  **Órdenes aparecen** en Bybit Testnet
-  **Estado**: Filled, Pending, o Cancelled
-  **Símbolos**: ETHUSDT, BTCUSDT, SOLUSDT
-  **Frecuencia**: Cada 15 minutos

---

##  **PASO 6: Testing y Validación**

### **Test de 1 Hora (4 señales)**
`ash
# Iniciar bot
.\start_bot.ps1

# Esperar 1 hora y verificar:
# - 4 señales generadas (cada 15 min)
# - 4 órdenes creadas en Bybit Testnet
# - Telegram recibe alertas
# - Grafana muestra métricas
`

### **Métricas a Verificar**
-  **Señales generadas**: 4 en 1 hora
-  **Órdenes creadas**: 4 en Bybit Testnet
-  **Balance**: Cambios en testnet
-  **Telegram**: 4 alertas recibidas
-  **Grafana**: Bot ONLINE, métricas activas

---

##  **TROUBLESHOOTING**

### **Problema: Bot no inicia**
`ash
# Verificar logs
Get-Content logs/system_init.log -Tail 20

# Verificar dependencias
python -c "import ccxt, requests, websocket"
`

### **Problema: No se generan señales**
`ash
# Verificar configuración
cat configs/strategies_config_optimized.json | grep -A 10 "VSTRU"

# Verificar implementación
grep -n "VSTRU" signal_engine.py
`

### **Problema: Órdenes no aparecen en Bybit**
`ash
# Verificar API keys
python -c "
import ccxt
exchange = ccxt.bybit({
    'apiKey': 'TU_API_KEY',
    'secret': 'TU_API_SECRET',
    'sandbox': True
})
print(exchange.fetch_balance())
"
`

---

##  **CHECKLIST DE VALIDACIÓN**

### ** Pre-requisitos**
- [ ] Scripts .ps1 funcionan
- [ ] Bot inicia correctamente
- [ ] Telegram recibe mensaje de inicio
- [ ] Grafana muestra bot ONLINE

### ** Estrategia VSTRU**
- [ ] VSTRU implementada en signal_engine.py
- [ ] VSTRU configurada en strategies_config_optimized.json
- [ ] VSTRU habilitada (enabled: true)
- [ ] Intervalo configurado a 15 minutos

### ** Conexión Bybit**
- [ ] API keys de testnet configuradas
- [ ] Bot conecta a Bybit Testnet
- [ ] WebSocket recibe datos en tiempo real
- [ ] API responde a requests

### ** Generación de Órdenes**
- [ ] Señales se generan cada 15 minutos
- [ ] Órdenes aparecen en Bybit Testnet
- [ ] Telegram recibe alertas de órdenes
- [ ] Grafana muestra métricas de trading

---

##  **RESULTADO ESPERADO**

**Después de 1 hora de testing:**
-  **4 señales** generadas (cada 15 min)
-  **4 órdenes** creadas en Bybit Testnet
-  **4 alertas** en Telegram
-  **Métricas activas** en Grafana
-  **Bot funcionando** correctamente

---

##  **CONTACTO**

Si encuentras problemas:
1. **Verificar logs** en logs/system_init.log
2. **Revisar configuración** en configs/
3. **Probar scripts** individualmente
4. **Validar API keys** de Bybit Testnet

**¡El objetivo es validar que las órdenes se crean REALMENTE en Bybit Testnet!** 
