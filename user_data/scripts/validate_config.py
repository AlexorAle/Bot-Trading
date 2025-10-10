#!/usr/bin/env python3
"""
Script de validación automática para archivos de configuración de Freqtrade.
Valida que el config tenga los campos requeridos antes de ejecutar backtests.
"""

import json
import sys
from pathlib import Path

def validate_config(config_path):
    """
    Valida que el archivo de configuración tenga los campos requeridos.
    
    Args:
        config_path (str): Ruta al archivo de configuración
        
    Returns:
        bool: True si es válido, False si hay errores
    """
    try:
        # Verificar que el archivo existe
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"❌ ERROR: El archivo {config_path} no existe")
            return False
        
        # Cargar el archivo JSON
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Lista de campos requeridos
        required_fields = [
            "stoploss",
            "minimal_roi",
            "exchange",
            "pairlists",
            "max_open_trades",
            "stake_currency",
            "stake_amount"
        ]
        
        # Verificar campos requeridos
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ ERROR: Faltan campos requeridos: {', '.join(missing_fields)}")
            return False
        
        # Verificar campos específicos
        errors = []
        
        # Verificar stoploss
        if not isinstance(config["stoploss"], (int, float)) or config["stoploss"] >= 0:
            errors.append("stoploss debe ser un número negativo")
        
        # Verificar minimal_roi
        if not isinstance(config["minimal_roi"], dict):
            errors.append("minimal_roi debe ser un objeto/diccionario")
        
        # Verificar exchange
        if "name" not in config["exchange"]:
            errors.append("exchange debe tener un campo 'name'")
        
        # Verificar strategy_parameters (opcional pero recomendado)
        if "strategy_parameters" not in config:
            print("⚠️  ADVERTENCIA: No se encontró 'strategy_parameters' en el config")
            print("   Esto es recomendado para parámetros personalizados de la estrategia")
        
        if errors:
            print(f"❌ ERROR: Problemas encontrados:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        # Mostrar información del config
        print("✅ Configuración válida")
        print(f"   - Stoploss: {config['stoploss']}")
        print(f"   - Minimal ROI: {config['minimal_roi']}")
        print(f"   - Exchange: {config['exchange']['name']}")
        print(f"   - Max open trades: {config['max_open_trades']}")
        print(f"   - Stake amount: {config['stake_amount']} {config['stake_currency']}")
        
        if "strategy_parameters" in config:
            print(f"   - Strategy parameters: {len(config['strategy_parameters'])} parámetros")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: El archivo JSON no es válido: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        return False

def main():
    """Función principal del script"""
    if len(sys.argv) != 2:
        print("Uso: python validate_config.py <ruta_al_config.json>")
        print("Ejemplo: python validate_config.py configs/config_crypto.json")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    print(f"🔍 Validando configuración: {config_path}")
    print("-" * 50)
    
    is_valid = validate_config(config_path)
    
    if is_valid:
        print("-" * 50)
        print("🎉 Configuración lista para usar")
        sys.exit(0)
    else:
        print("-" * 50)
        print("💥 Configuración inválida - Corregir antes de continuar")
        sys.exit(1)

if __name__ == "__main__":
    main()

