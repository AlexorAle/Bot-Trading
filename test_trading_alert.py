#!/usr/bin/env python3
"""
Simulación de la herramienta trading_alert
"""
from datetime import datetime

def simulate_trading_alert(drawdown, reason, portfolio_value=None):
    """Simula la ejecución de la herramienta trading_alert"""
    alert_message = "🚨 ALERTA CRÍTICA DE TRADING 🚨\n"
    alert_message += f"Drawdown: {drawdown}%\n"
    alert_message += f"Razón: {reason}\n"
    if portfolio_value:
        alert_message += f"Valor del Portfolio: ${portfolio_value:,.2f}\n"
    alert_message += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    result = f"✅ Alerta de trading procesada:\n{alert_message}"
    return result

if __name__ == "__main__":
    # Ejecutar con los parámetros que proporcionaste
    result = simulate_trading_alert(5.2, "Drawdown excesivo detectado", 10000.50)
    print(result)




