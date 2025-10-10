# 🤖 BOT Trading - Liquidation Hunter Strategy

## 📋 **Descripción del Proyecto**

Sistema de trading automatizado que implementa la estrategia **Liquidation Hunter** usando Backtrader. Diseñado para operar en múltiples mercados (Crypto, Forex, Índices) con alta flexibilidad y escalabilidad.

## 🎯 **Características Principales**

- **🔄 Multi-Mercado**: Soporte para Crypto (ETH/USDT) y Forex (EUR/USD)
- **🧠 ML-Enhanced**: Combina Kalman Filter con predicciones ML-like
- **⚡ Backtrader Engine**: Motor de backtesting robusto y flexible
- **📊 Análisis Integrado**: Sharpe Ratio, Drawdown, Trade Analysis
- **⚙️ Configuración JSON**: Parámetros centralizados por mercado
- **📈 Escalable**: Arquitectura modular para 5+ estrategias

## 🏗️ **Arquitectura**

```
backtrader_engine/
├── data/                    # 📊 Datos de mercado
├── strategies/              # 🎯 Estrategias de trading
├── configs/                 # ⚙️ Configuraciones JSON
├── engine/                  # 🔧 Motor de ejecución
├── reports/                 # 📈 Reportes y análisis
└── main.py                  # 🚀 Punto de entrada
```

## 🚀 **Instalación Rápida**

### **1. Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/bot-trading.git
cd bot-trading
```

### **2. Instalar dependencias**
```bash
pip install backtrader pandas matplotlib numpy
```

### **3. Configurar datos**
- Colocar archivos CSV en `backtrader_engine/data/`
- Formato: `datetime,open,high,low,close,volume`

### **4. Ejecutar backtest**
```bash
cd backtrader_engine
python main.py --config configs/config_eth.json
```

## 📊 **Estrategias Disponibles**

### **LiquidationHunterStrategy**
- **Kalman Filter**: Detección de tendencias
- **ML Predictions**: RSI + EMA crossovers
- **Risk Management**: Stop loss y take profit automáticos
- **Parámetros**: Configurables por JSON

### **SimpleTestStrategy**
- **RSI Strategy**: Estrategia básica para testing
- **Risk Management**: Stop loss y take profit
- **Ideal para**: Validación del sistema

## ⚙️ **Configuración**

### **Parámetros Kalman Filter**
```json
{
  "kalman_threshold": 0.3,
  "deviation_threshold": 1.5,
  "ml_confidence_threshold": 0.55
}
```

### **Parámetros Técnicos**
```json
{
  "rsi_period": 14,
  "ema_fast_period": 8,
  "ema_slow_period": 21
}
```

### **Gestión de Riesgo**
```json
{
  "stop_loss": 0.03,
  "take_profit": 0.06,
  "position_size": 0.95
}
```

## 🎮 **Uso**

### **Backtest Crypto (ETH/USDT)**
```bash
python main.py --config configs/config_eth.json
```

### **Backtest Forex (EUR/USD)**
```bash
python main.py --config configs/config_eurusd.json
```

### **Test Simple**
```bash
python main.py --config configs/config_simple.json
```

## 📈 **Métricas de Performance**

- **Sharpe Ratio**: Medida de riesgo-ajustado
- **Maximum Drawdown**: Pérdida máxima
- **Total Returns**: Retorno total
- **Win Rate**: Porcentaje de trades ganadores
- **Trade Analysis**: Estadísticas detalladas

## 🔧 **Desarrollo**

### **Agregar Nueva Estrategia**
1. Crear archivo en `strategies/nueva_estrategia.py`
2. Heredar de `bt.Strategy`
3. Implementar métodos `__init__()` y `next()`
4. Agregar configuración en `configs/`

### **Agregar Nuevo Mercado**
1. Crear `configs/config_nuevo_mercado.json`
2. Ajustar comisiones y parámetros
3. Preparar datos en formato CSV

## 📋 **Roadmap**

- [x] **v1.0**: Migración de Freqtrade a Backtrader
- [x] **v1.0**: Soporte multi-mercado
- [x] **v1.0**: Sistema de configuración JSON
- [ ] **v1.1**: Optimización de parámetros
- [ ] **v1.2**: Trading en vivo
- [ ] **v1.3**: Interfaz web
- [ ] **v1.4**: Machine Learning avanzado

## 🐛 **Problemas Conocidos**

- **RSI Error**: Requiere datos reales para validación completa
- **Plot Generation**: Puede fallar en algunos entornos

## 📞 **Soporte**

Para reportar bugs o solicitar features:
1. Crear un Issue en GitHub
2. Incluir logs y configuración
3. Describir el comportamiento esperado

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🤝 **Contribuciones**

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**Versión**: 1.0.0  
**Última actualización**: 2025-01-10  
**Autor**: Tu Nombre
