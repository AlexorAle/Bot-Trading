#!/usr/bin/env python3
"""
ejemplo_integracion_cursor.py - Ejemplo de cómo integrar GitOps_Watcher con Cursor
================================================================================

Este archivo muestra cómo integrar la lógica de bloqueo del GitOps_Watcher_Agent
en tu flujo de trabajo con Cursor y otros agentes.
"""

from gitops_blocking_logic import check_git_operation_safety, validate_critical_operation
import subprocess
import sys

def execute_git_operation_with_protection(operation, **kwargs):
    """
    Ejecuta una operación Git con protección del GitOps_Watcher_Agent.
    
    Args:
        operation: Tipo de operación (merge, push, etc.)
        **kwargs: Argumentos adicionales (target_branch, source_branch, etc.)
    """
    print(f"🔍 Verificando seguridad de operación: {operation}")
    
    # 1. Verificar seguridad antes de ejecutar
    is_safe, message, critical_files = check_git_operation_safety(
        operation, 
        kwargs.get('target_branch'),
        kwargs.get('source_branch')
    )
    
    if not is_safe:
        # 2. BLOQUEAR OPERACIÓN
        print(f"\n🚨 OPERACIÓN BLOQUEADA 🚨")
        print(f"Razón: {message}")
        
        if critical_files:
            print(f"\nArchivos críticos afectados:")
            for file in critical_files:
                print(f"  ⚠️ {file}")
        
        # 3. Solicitar confirmación explícita
        print(f"\n¿Deseas continuar con esta operación?")
        print(f"Para proceder, escribe exactamente:")
        
        if operation == "merge":
            confirmation_required = "CONFIRMO MERGE CRÍTICO"
        elif operation == "push":
            target_branch = kwargs.get('target_branch', 'main')
            confirmation_required = f"CONFIRMO PUSH CRÍTICO A {target_branch.upper()}"
        else:
            confirmation_required = f"CONFIRMO {operation.upper()}"
        
        print(f"'{confirmation_required}'")
        
        # 4. Esperar confirmación del usuario
        user_input = input("\nTu confirmación: ").strip()
        
        # 5. Validar confirmación
        if not validate_critical_operation(operation, user_input, **kwargs):
            print("❌ Confirmación inválida. Operación cancelada.")
            return False, "Operación cancelada - confirmación inválida"
        
        print("✅ Confirmación válida. Procediendo con la operación...")
    
    # 6. Ejecutar operación Git
    try:
        if operation == "merge":
            source_branch = kwargs.get('source_branch')
            if source_branch:
                result = subprocess.run(['git', 'merge', source_branch], 
                                      capture_output=True, text=True)
            else:
                return False, "Rama origen no especificada para merge"
                
        elif operation == "push":
            target_branch = kwargs.get('target_branch', 'main')
            result = subprocess.run(['git', 'push', 'origin', target_branch], 
                                  capture_output=True, text=True)
        else:
            return False, f"Operación {operation} no implementada"
        
        if result.returncode == 0:
            print(f"✅ Operación {operation} ejecutada exitosamente")
            return True, "Operación exitosa"
        else:
            print(f"❌ Error en operación {operation}: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ Error ejecutando operación: {e}")
        return False, str(e)

def ejemplo_uso():
    """Ejemplo de cómo usar la integración."""
    print("=== EJEMPLO DE INTEGRACIÓN GITOPS_WATCHER ===\n")
    
    # Ejemplo 1: Merge seguro (archivos no críticos)
    print("1. Intentando merge seguro...")
    success, message = execute_git_operation_with_protection(
        "merge", 
        target_branch="main", 
        source_branch="feature/documentation"
    )
    print(f"Resultado: {success} - {message}\n")
    
    # Ejemplo 2: Push a main (podría ser peligroso)
    print("2. Intentando push a main...")
    success, message = execute_git_operation_with_protection(
        "push", 
        target_branch="main"
    )
    print(f"Resultado: {success} - {message}\n")

if __name__ == "__main__":
    ejemplo_uso()
