#!/usr/bin/env python3
"""
Script para listar las herramientas MCP disponibles
"""
import asyncio
import json
import subprocess
import sys
import time

def list_mcp_tools():
    """Lista las herramientas MCP disponibles"""
    print("🛠️  HERRAMIENTAS MCP DISPONIBLES:")
    print("=" * 50)
    
    # Herramientas disponibles en el servidor MCP
    tools = [
        {
            "name": "slack_send_message",
            "description": "Envía un mensaje a un canal de Slack",
            "parameters": {
                "channel": "Canal de Slack (ej: #general)",
                "message": "Mensaje a enviar"
            }
        },
        {
            "name": "gmail_send_email", 
            "description": "Envía un email usando Gmail",
            "parameters": {
                "to": "Dirección de email destino",
                "subject": "Asunto del email",
                "body": "Cuerpo del email"
            }
        },
        {
            "name": "google_sheets_append_row",
            "description": "Agrega una fila a una hoja de Google Sheets",
            "parameters": {
                "spreadsheet_id": "ID de la hoja de cálculo",
                "sheet_name": "Nombre de la hoja",
                "values": "Valores a agregar (array)"
            }
        },
        {
            "name": "trading_alert",
            "description": "🚨 Envía una alerta crítica del bot de trading",
            "parameters": {
                "drawdown": "Porcentaje de drawdown (número)",
                "reason": "Razón de la alerta (texto)",
                "portfolio_value": "Valor actual del portfolio (opcional)"
            }
        }
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. {tool['name']}")
        print(f"   📝 {tool['description']}")
        print("   📋 Parámetros:")
        for param, desc in tool['parameters'].items():
            print(f"      - {param}: {desc}")
    
    print("\n" + "=" * 50)
    print("✅ Total de herramientas: 4")
    print("🎯 Herramienta principal para tu bot: trading_alert")
    print("\n💡 Para usar en Cursor IDE:")
    print("   'Usa la herramienta trading_alert con drawdown 5.2, razón \"Drawdown excesivo\"'")

if __name__ == "__main__":
    list_mcp_tools()




