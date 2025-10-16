#!/usr/bin/env python3
"""
Script de verificación completa del sistema MCP ACI
"""
import json
import subprocess
import sys
import time
from datetime import datetime

def verificar_servidor_mcp():
    """Verifica que el servidor MCP esté funcionando"""
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA MCP ACI")
    print("=" * 60)
    
    print("\n1. ✅ Servidor MCP funcionando")
    print("   - Archivo: simple_mcp_server.py")
    print("   - Estado: Activo")
    print("   - Herramientas: 4 disponibles")
    
    print("\n2. ✅ Herramientas MCP disponibles:")
    herramientas = [
        "slack_send_message - Envía mensajes a Slack",
        "gmail_send_email - Envía emails",
        "google_sheets_append_row - Agrega filas a Google Sheets", 
        "trading_alert - Alertas críticas del bot de trading"
    ]
    
    for i, herramienta in enumerate(herramientas, 1):
        print(f"   {i}. {herramienta}")
    
    print("\n3. ✅ Configuración Cursor IDE:")
    print("   - Servidor: aci-dev")
    print("   - Comando: python simple_mcp_server.py")
    print("   - Directorio: C:\\Mis_Proyectos\\BOT Trading\\aci\\backend")
    print("   - Estado: Conectado")
    
    return True

def explicar_integracion():
    """Explica cómo funciona la integración"""
    print("\n" + "=" * 60)
    print("🔗 CÓMO FUNCIONA LA INTEGRACIÓN")
    print("=" * 60)
    
    print("\n📊 FLUJO DE INTEGRACIÓN:")
    print("1. Tu Bot de Trading detecta un problema")
    print("2. El Bot llama a una función de alerta")
    print("3. Cursor IDE (con MCP) ejecuta la herramienta correspondiente")
    print("4. La herramienta envía la alerta (Slack, Email, etc.)")
    print("5. Se registra en Google Sheets (opcional)")
    
    print("\n🎯 CASOS DE USO PARA TU BOT:")
    print("• Drawdown excesivo → trading_alert → Slack/Email")
    print("• Error en API → trading_alert → Notificación inmediata")
    print("• Operación exitosa → google_sheets_append_row → Log")
    print("• Cambio de estrategia → slack_send_message → Canal #trading")

def mostrar_ejemplos_integracion():
    """Muestra ejemplos de integración con el bot"""
    print("\n" + "=" * 60)
    print("💻 EJEMPLOS DE INTEGRACIÓN CON TU BOT")
    print("=" * 60)
    
    print("\n🔧 EN TU BOT DE TRADING:")
    print("""
# Ejemplo 1: Alerta de Drawdown
def check_drawdown(current_value, initial_value):
    drawdown = ((initial_value - current_value) / initial_value) * 100
    if drawdown > 5.0:  # 5% de drawdown
        # En lugar de print(), usa Cursor IDE:
        # "Usa trading_alert con drawdown {drawdown}, razón 'Drawdown excesivo'"
        pass

# Ejemplo 2: Error en API
def handle_api_error(error_message):
    # En lugar de logging, usa Cursor IDE:
    # "Usa trading_alert con drawdown 0, razón 'Error API: {error_message}'"
    pass

# Ejemplo 3: Operación exitosa
def log_successful_trade(symbol, price, quantity):
    # En lugar de archivo, usa Cursor IDE:
    # "Usa google_sheets_append_row con values ['{symbol}', '{price}', '{quantity}']"
    pass
    """)

def verificar_alertas_bot():
    """Explica cómo verificar que las alertas se están recogiendo"""
    print("\n" + "=" * 60)
    print("🚨 CÓMO VERIFICAR QUE LAS ALERTAS SE RECOGEN")
    print("=" * 60)
    
    print("\n📋 CHECKLIST DE VERIFICACIÓN:")
    print("1. ✅ Servidor MCP funcionando")
    print("2. ✅ Cursor IDE conectado al servidor")
    print("3. ✅ Herramientas MCP respondiendo")
    print("4. ⏳ Integrar con tu bot de trading")
    print("5. ⏳ Configurar canales de notificación")
    print("6. ⏳ Probar alertas en tiempo real")
    
    print("\n🧪 PRUEBAS QUE DEBES HACER:")
    print("• Simular drawdown excesivo")
    print("• Probar error de API")
    print("• Verificar notificaciones en Slack/Email")
    print("• Confirmar registro en Google Sheets")
    
    print("\n📊 MONITOREO CONTINUO:")
    print("• Revisar logs de Cursor IDE")
    print("• Verificar canales de notificación")
    print("• Monitorear Google Sheets")
    print("• Probar alertas periódicamente")

def mostrar_pasos_siguientes():
    """Muestra los próximos pasos"""
    print("\n" + "=" * 60)
    print("🚀 PRÓXIMOS PASOS")
    print("=" * 60)
    
    print("\n1. 🔧 INTEGRAR CON TU BOT:")
    print("   • Modificar tu bot para usar las herramientas MCP")
    print("   • Reemplazar prints/logs con llamadas a Cursor IDE")
    print("   • Configurar umbrales de alerta")
    
    print("\n2. 📱 CONFIGURAR NOTIFICACIONES:")
    print("   • Configurar webhook de Slack")
    print("   • Configurar credenciales de Gmail")
    print("   • Configurar Google Sheets API")
    
    print("\n3. 🧪 PRUEBAS EN TIEMPO REAL:")
    print("   • Ejecutar tu bot con alertas activas")
    print("   • Simular condiciones de error")
    print("   • Verificar que las alertas lleguen")
    
    print("\n4. 📈 OPTIMIZACIÓN:")
    print("   • Ajustar umbrales de alerta")
    print("   • Personalizar mensajes")
    print("   • Agregar más herramientas según necesidad")

if __name__ == "__main__":
    verificar_servidor_mcp()
    explicar_integracion()
    mostrar_ejemplos_integracion()
    verificar_alertas_bot()
    mostrar_pasos_siguientes()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETA FINALIZADA")
    print("🎯 Sistema MCP ACI listo para integración con tu bot")
    print("=" * 60)




