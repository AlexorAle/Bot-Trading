"""
Script para configurar Telegram con el bot de trading
"""

import json
import requests
from pathlib import Path

def setup_telegram():
    """Configurar Telegram para alertas del bot"""
    
    print("🤖 Configuración de Telegram para Alertas del Bot")
    print("=" * 60)
    
    print("\n📋 PASOS PARA CONFIGURAR TELEGRAM:")
    print("1. Abre Telegram y busca @BotFather")
    print("2. Envía /newbot")
    print("3. Elige un nombre para tu bot (ej: 'Mi Bot de Trading')")
    print("4. Elige un username (debe terminar en 'bot', ej: 'mi_trading_bot')")
    print("5. Copia el TOKEN que te da BotFather")
    print("6. Para obtener tu CHAT_ID, envía un mensaje a tu bot y luego visita:")
    print("   https://api.telegram.org/bot<TOKEN>/getUpdates")
    print("   Busca 'chat':{'id': NUMERO}")
    
    print("\n" + "=" * 60)
    
    # Solicitar configuración
    bot_token = input("🔑 Ingresa tu Bot Token: ").strip()
    chat_id = input("💬 Ingresa tu Chat ID: ").strip()
    
    if not bot_token or not chat_id:
        print("❌ Error: Bot Token y Chat ID son requeridos")
        return False
    
    # Probar conexión
    print("\n🔍 Probando conexión con Telegram...")
    
    try:
        # Probar con getMe
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('first_name', 'Unknown')
            bot_username = bot_info.get('username', 'Unknown')
            
            print(f"✅ Conexión exitosa!")
            print(f"   Bot: {bot_name} (@{bot_username})")
            
            # Probar envío de mensaje
            test_message = "🤖 Bot de Trading configurado correctamente!\n\n✅ Conexión establecida\n📊 Alertas habilitadas\n🚀 Listo para operar"
            
            send_response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={
                    'chat_id': chat_id,
                    'text': test_message,
                    'parse_mode': 'HTML'
                },
                timeout=10
            )
            
            if send_response.status_code == 200:
                print("✅ Mensaje de prueba enviado correctamente!")
            else:
                print(f"⚠️  Error enviando mensaje de prueba: {send_response.status_code}")
                print("   Verifica que tu Chat ID sea correcto")
                return False
            
        else:
            print(f"❌ Error de conexión: {response.status_code}")
            print("   Verifica que tu Bot Token sea correcto")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    # Guardar configuración
    print("\n💾 Guardando configuración...")
    
    try:
        # Cargar configuración actual
        config_path = Path("configs/alert_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Actualizar configuración de Telegram
        config['telegram']['enabled'] = True
        config['telegram']['bot_token'] = bot_token
        config['telegram']['chat_id'] = chat_id
        
        # Guardar configuración
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuración guardada en configs/alert_config.json")
        
        # Mostrar resumen
        print("\n📊 RESUMEN DE CONFIGURACIÓN:")
        print(f"   Bot: {bot_name} (@{bot_username})")
        print(f"   Chat ID: {chat_id}")
        print(f"   Archivo: configs/alert_config.json")
        
        print("\n🎉 ¡Configuración completada!")
        print("   El bot ahora enviará alertas a tu Telegram")
        
        return True
        
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False

def test_telegram_config():
    """Probar configuración de Telegram existente"""
    
    print("🔍 Probando configuración de Telegram existente...")
    
    try:
        # Cargar configuración
        config_path = Path("configs/alert_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        telegram_config = config.get('telegram', {})
        
        if not telegram_config.get('enabled', False):
            print("❌ Telegram no está habilitado en la configuración")
            return False
        
        bot_token = telegram_config.get('bot_token')
        chat_id = telegram_config.get('chat_id')
        
        if not bot_token or not chat_id:
            print("❌ Bot Token o Chat ID no configurados")
            return False
        
        # Probar conexión
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('first_name', 'Unknown')
            bot_username = bot_info.get('username', 'Unknown')
            
            print(f"✅ Configuración válida!")
            print(f"   Bot: {bot_name} (@{bot_username})")
            print(f"   Chat ID: {chat_id}")
            
            return True
        else:
            print(f"❌ Error de conexión: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando configuración: {e}")
        return False

def main():
    """Función principal"""
    
    print("🤖 Configurador de Telegram para Bot de Trading")
    print("=" * 60)
    
    while True:
        print("\n📋 OPCIONES:")
        print("1. Configurar Telegram (nuevo)")
        print("2. Probar configuración existente")
        print("3. Salir")
        
        choice = input("\n🔢 Selecciona una opción (1-3): ").strip()
        
        if choice == "1":
            if setup_telegram():
                print("\n✅ Configuración completada exitosamente!")
            else:
                print("\n❌ Error en la configuración")
        
        elif choice == "2":
            if test_telegram_config():
                print("\n✅ Configuración funcionando correctamente!")
            else:
                print("\n❌ Problema con la configuración")
        
        elif choice == "3":
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("\n❌ Opción inválida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
