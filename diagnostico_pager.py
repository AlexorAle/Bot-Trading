#!/usr/bin/env python3
"""
diagnostico_pager.py - Diagnóstico del Problema de Pager
=======================================================

Este script diagnostica y soluciona el problema del terminal pager
que impide la ejecución automática de comandos Git por parte de los agentes.
"""

import subprocess
import os
import sys
import time

def test_git_command(command, description):
    """
    Prueba un comando Git y verifica si funciona sin pager.
    
    Args:
        command: Comando Git a probar
        description: Descripción del comando
    """
    print(f"\n🔍 Probando: {description}")
    print(f"Comando: {command}")
    
    try:
        # Configurar variables de entorno para evitar pager
        env = os.environ.copy()
        env['GIT_PAGER'] = 'cat'
        env['PAGER'] = 'cat'
        
        # Agregar --no-pager si no está presente
        if command.startswith('git ') and '--no-pager' not in command:
            command = command.replace('git ', 'git --no-pager ', 1)
        
        start_time = time.time()
        
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=env,
            timeout=10  # Timeout de 10 segundos para diagnóstico
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ ÉXITO - Tiempo: {execution_time:.2f}s")
            print(f"Output (primeras 3 líneas):")
            lines = result.stdout.strip().split('\n')[:3]
            for line in lines:
                print(f"  {line}")
            lines_count = len(result.stdout.strip().split('\n'))
            if lines_count > 3:
                print(f"  ... y {lines_count - 3} líneas más")
            return True
        else:
            print(f"❌ ERROR - Código: {result.returncode}")
            print(f"Stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - Comando tardó más de 10 segundos")
        return False
    except Exception as e:
        print(f"💥 EXCEPCIÓN: {e}")
        return False

def check_git_config():
    """Verifica la configuración actual de Git."""
    print("🔧 Verificando configuración de Git...")
    
    try:
        # Verificar configuración de pager
        result = subprocess.run(
            ['git', 'config', '--global', 'core.pager'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pager_config = result.stdout.strip()
            print(f"Configuración de pager: '{pager_config}'")
            
            if pager_config == 'cat' or pager_config == '':
                print("✅ Configuración correcta - sin pager")
                return True
            else:
                print("⚠️ Configuración con pager - puede causar problemas")
                return False
        else:
            print("❌ No se pudo obtener configuración de pager")
            return False
            
    except Exception as e:
        print(f"💥 Error verificando configuración: {e}")
        return False

def fix_git_config():
    """Soluciona la configuración de Git para evitar problemas de pager."""
    print("\n🔧 Solucionando configuración de Git...")
    
    try:
        # Configurar pager como cat
        result = subprocess.run(
            ['git', 'config', '--global', 'core.pager', 'cat'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Configuración de pager actualizada")
            return True
        else:
            print(f"❌ Error actualizando configuración: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 Error solucionando configuración: {e}")
        return False

def run_diagnosis():
    """Ejecuta el diagnóstico completo."""
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DEL PROBLEMA DE PAGER")
    print("=" * 60)
    
    # 1. Verificar configuración actual
    config_ok = check_git_config()
    
    # 2. Si no está bien configurado, solucionarlo
    if not config_ok:
        print("\n🔧 Solucionando configuración...")
        fix_git_config()
        print("✅ Configuración solucionada")
    
    # 3. Probar comandos Git críticos
    print("\n" + "=" * 60)
    print("🧪 PROBANDO COMANDOS GIT CRÍTICOS")
    print("=" * 60)
    
    test_commands = [
        ("git log --oneline -n 3", "Log de commits recientes"),
        ("git status --porcelain", "Estado del repositorio"),
        ("git branch -r", "Ramas remotas"),
        ("git diff HEAD~1..HEAD", "Diferencias del último commit"),
        ("git config --list", "Configuración de Git")
    ]
    
    results = []
    for command, description in test_commands:
        success = test_git_command(command, description)
        results.append(success)
    
    # 4. Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    successful_tests = sum(results)
    total_tests = len(results)
    
    print(f"Pruebas exitosas: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 ¡TODOS LOS COMANDOS FUNCIONAN CORRECTAMENTE!")
        print("✅ El problema del pager está solucionado")
        print("✅ Los agentes pueden ejecutar comandos Git automáticamente")
    else:
        print("⚠️ Algunos comandos fallaron")
        print("❌ Puede haber problemas con la ejecución automática")
    
    # 5. Recomendaciones
    print("\n" + "=" * 60)
    print("💡 RECOMENDACIONES")
    print("=" * 60)
    
    if successful_tests == total_tests:
        print("✅ El sistema está listo para usar")
        print("✅ Puedes ejecutar: python run_git_watcher.py")
        print("✅ Los agentes pueden ejecutar comandos Git sin problemas")
    else:
        print("🔧 Acciones recomendadas:")
        print("1. Verificar que Git está instalado correctamente")
        print("2. Verificar permisos de ejecución")
        print("3. Revisar variables de entorno")
        print("4. Considerar reinstalar Git si es necesario")
    
    return successful_tests == total_tests

def test_gitops_watcher():
    """Prueba específica del GitOps_Watcher_Agent."""
    print("\n" + "=" * 60)
    print("🤖 PROBANDO GITOPS_WATCHER_AGENT")
    print("=" * 60)
    
    try:
        from git_watcher import GitOpsWatcher
        
        print("✅ Importación exitosa de GitOpsWatcher")
        
        # Crear instancia
        watcher = GitOpsWatcher()
        print("✅ Instancia creada exitosamente")
        
        # Probar comando Git
        success, output = watcher.execute_git_command("git log --oneline -n 2")
        
        if success:
            print("✅ Comando Git ejecutado exitosamente")
            print(f"Output: {output[:100]}...")
        else:
            print(f"❌ Error ejecutando comando Git: {output}")
        
        return success
        
    except ImportError as e:
        print(f"❌ Error importando GitOpsWatcher: {e}")
        return False
    except Exception as e:
        print(f"❌ Error probando GitOpsWatcher: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico del problema de pager...")
    
    # Ejecutar diagnóstico principal
    diagnosis_ok = run_diagnosis()
    
    # Probar GitOps_Watcher_Agent específicamente
    gitops_ok = test_gitops_watcher()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("🏁 RESULTADO FINAL")
    print("=" * 60)
    
    if diagnosis_ok and gitops_ok:
        print("🎉 ¡DIAGNÓSTICO COMPLETO EXITOSO!")
        print("✅ El problema del pager está solucionado")
        print("✅ GitOps_Watcher_Agent está funcionando correctamente")
        print("✅ Los agentes pueden ejecutar comandos Git automáticamente")
        sys.exit(0)
    else:
        print("⚠️ DIAGNÓSTICO CON PROBLEMAS")
        if not diagnosis_ok:
            print("❌ Problemas con comandos Git básicos")
        if not gitops_ok:
            print("❌ Problemas con GitOps_Watcher_Agent")
        print("🔧 Revisar las recomendaciones anteriores")
        sys.exit(1)
