#!/usr/bin/env python3
"""
gitops_blocking_logic.py - Lógica de Bloqueo del Agente Principal
================================================================

Este módulo integra la lógica de bloqueo del GitOps_Watcher_Agent en el
Agente Principal de Cursor. Previene operaciones críticas sin consulta del usuario.

Funcionalidades:
- Detección automática de cambios en archivos críticos
- Bloqueo de operaciones de merge/push peligrosas
- Consulta obligatoria al usuario
- Integración con el sistema de notificaciones
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from git_watcher import GitOpsWatcher

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitOpsBlockingLogic:
    """
    Clase que implementa la lógica de bloqueo para el Agente Principal.
    Se integra con Cursor para prevenir operaciones críticas.
    """
    
    def __init__(self):
        """Inicializa la lógica de bloqueo."""
        self.watcher = GitOpsWatcher()
        
        # Archivos críticos que requieren consulta obligatoria
        self.CRITICAL_FILES = [
            "risk_parity_allocator.py",
            "broker_handler.py", 
            "portfolio_engine.py",
            "main.py",
            "config.py",
            "execution/trader.py",
            "strategy/liquidation_hunter.py"
        ]
        
        # Operaciones que requieren validación
        self.CRITICAL_OPERATIONS = [
            "merge",
            "push",
            "rebase",
            "force_push",
            "reset"
        ]
        
        logger.info("GitOps Blocking Logic inicializada")
    
    def check_operation_safety(self, operation: str, target_branch: str = None, 
                             source_branch: str = None) -> Tuple[bool, str, List[str]]:
        """
        Verifica si una operación es segura de ejecutar.
        
        Args:
            operation: Tipo de operación (merge, push, etc.)
            target_branch: Rama objetivo (para merge)
            source_branch: Rama origen (para merge)
            
        Returns:
            Tuple[bool, str, List[str]]: (es_segura, mensaje, archivos_críticos)
        """
        logger.info(f"Verificando seguridad de operación: {operation}")
        
        if operation not in self.CRITICAL_OPERATIONS:
            return True, "Operación no crítica", []
        
        # Para operaciones de merge, verificar diferencias
        if operation == "merge" and target_branch and source_branch:
            return self._check_merge_safety(target_branch, source_branch)
        
        # Para push, verificar cambios locales
        elif operation == "push" and target_branch:
            return self._check_push_safety(target_branch)
        
        # Para otras operaciones, verificación básica
        return self._check_general_safety(operation, target_branch)
    
    def _check_merge_safety(self, target_branch: str, source_branch: str) -> Tuple[bool, str, List[str]]:
        """
        Verifica la seguridad de una operación de merge.
        
        Args:
            target_branch: Rama objetivo del merge
            source_branch: Rama origen del merge
            
        Returns:
            Tuple[bool, str, List[str]]: (es_segura, mensaje, archivos_críticos)
        """
        logger.info(f"Verificando seguridad de merge: {source_branch} -> {target_branch}")
        
        try:
            # Obtener diff entre las ramas
            success, diff_content = self.watcher.execute_git_command(
                f"git diff {target_branch}..{source_branch}"
            )
            
            if not success:
                return False, f"Error obteniendo diff entre {target_branch} y {source_branch}", []
            
            # Verificar archivos críticos
            critical_files_changed = self.watcher.check_critical_files_changed(diff_content)
            
            if critical_files_changed:
                # Bloqueo requerido
                message = f"""
🚨 OPERACIÓN BLOQUEADA - ARCHIVOS CRÍTICOS DETECTADOS 🚨

Se encontraron cambios en archivos críticos en el merge:
{target_branch} <- {source_branch}

Archivos críticos modificados:
{chr(10).join([f"• {file}" for file in critical_files_changed])}

⚠️ ACCIÓN REQUERIDA: Confirma explícitamente que deseas continuar con esta operación.

Para proceder, responde con: "CONFIRMO MERGE CRÍTICO"
"""
                
                # Enviar alerta crítica
                self._send_critical_alert(message, critical_files_changed, operation="merge")
                
                return False, message, critical_files_changed
            else:
                return True, f"Merge seguro: {source_branch} -> {target_branch}", []
                
        except Exception as e:
            logger.error(f"Error verificando merge: {e}")
            return False, f"Error verificando merge: {e}", []
    
    def _check_push_safety(self, target_branch: str) -> Tuple[bool, str, List[str]]:
        """
        Verifica la seguridad de una operación de push.
        
        Args:
            target_branch: Rama objetivo del push
            
        Returns:
            Tuple[bool, str, List[str]]: (es_segura, mensaje, archivos_críticos)
        """
        logger.info(f"Verificando seguridad de push a: {target_branch}")
        
        try:
            # Verificar si es push a rama main
            if target_branch in ["main", "master"]:
                # Obtener cambios locales
                success, diff_content = self.watcher.execute_git_command(
                    f"git diff HEAD~1..HEAD"
                )
                
                if not success:
                    return False, f"Error obteniendo cambios locales", []
                
                # Verificar archivos críticos
                critical_files_changed = self.watcher.check_critical_files_changed(diff_content)
                
                if critical_files_changed:
                    message = f"""
🚨 PUSH BLOQUEADO - CAMBIOS CRÍTICOS A MAIN 🚨

Se detectaron cambios en archivos críticos en el push a {target_branch}:

Archivos críticos modificados:
{chr(10).join([f"• {file}" for file in critical_files_changed])}

⚠️ ACCIÓN REQUERIDA: Confirma explícitamente que deseas hacer push a {target_branch}.

Para proceder, responde con: "CONFIRMO PUSH CRÍTICO A {target_branch.upper()}"
"""
                    
                    # Enviar alerta crítica
                    self._send_critical_alert(message, critical_files_changed, operation="push")
                    
                    return False, message, critical_files_changed
                else:
                    return True, f"Push seguro a {target_branch}", []
            else:
                return True, f"Push a rama no crítica: {target_branch}", []
                
        except Exception as e:
            logger.error(f"Error verificando push: {e}")
            return False, f"Error verificando push: {e}", []
    
    def _check_general_safety(self, operation: str, target_branch: str = None) -> Tuple[bool, str, List[str]]:
        """
        Verificación general de seguridad para otras operaciones.
        
        Args:
            operation: Tipo de operación
            target_branch: Rama objetivo
            
        Returns:
            Tuple[bool, str, List[str]]: (es_segura, mensaje, archivos_críticos)
        """
        logger.info(f"Verificación general de seguridad para: {operation}")
        
        # Para operaciones como rebase, reset, etc.
        if target_branch in ["main", "master"]:
            message = f"""
⚠️ OPERACIÓN CRÍTICA DETECTADA ⚠️

Se intenta ejecutar {operation} en la rama {target_branch}.

Esta operación puede afectar archivos críticos del sistema.

¿Deseas continuar? Responde con: "CONFIRMO {operation.upper()}"
"""
            return False, message, []
        else:
            return True, f"Operación {operation} permitida en {target_branch}", []
    
    def _send_critical_alert(self, message: str, critical_files: List[str], operation: str):
        """
        Envía una alerta crítica por Slack.
        
        Args:
            message: Mensaje de la alerta
            critical_files: Lista de archivos críticos
            operation: Tipo de operación bloqueada
        """
        try:
            # Enviar alerta usando el watcher
            self.watcher.send_audit_alert(message, "trading-gitops")
            logger.warning(f"Alerta crítica enviada para operación: {operation}")
            
        except Exception as e:
            logger.error(f"Error enviando alerta crítica: {e}")
    
    def validate_user_confirmation(self, user_response: str, operation: str, 
                                 target_branch: str = None) -> bool:
        """
        Valida la confirmación del usuario para operaciones críticas.
        
        Args:
            user_response: Respuesta del usuario
            operation: Tipo de operación
            target_branch: Rama objetivo
            
        Returns:
            bool: True si la confirmación es válida
        """
        logger.info(f"Validando confirmación del usuario para: {operation}")
        
        # Patrones de confirmación válidos
        confirmation_patterns = {
            "merge": ["CONFIRMO MERGE CRÍTICO", "CONFIRMO MERGE"],
            "push": [f"CONFIRMO PUSH CRÍTICO A {target_branch.upper()}" if target_branch else "CONFIRMO PUSH CRÍTICO"],
            "rebase": ["CONFIRMO REBASE"],
            "reset": ["CONFIRMO RESET"],
            "force_push": ["CONFIRMO FORCE PUSH"]
        }
        
        if operation in confirmation_patterns:
            valid_patterns = confirmation_patterns[operation]
            user_upper = user_response.upper().strip()
            
            for pattern in valid_patterns:
                if pattern in user_upper:
                    logger.info(f"Confirmación válida recibida para {operation}")
                    return True
        
        logger.warning(f"Confirmación inválida para {operation}: {user_response}")
        return False
    
    def execute_safe_operation(self, operation: str, **kwargs) -> Tuple[bool, str]:
        """
        Ejecuta una operación de forma segura con validaciones.
        
        Args:
            operation: Tipo de operación a ejecutar
            **kwargs: Argumentos adicionales para la operación
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        logger.info(f"Ejecutando operación segura: {operation}")
        
        # Verificar seguridad
        is_safe, message, critical_files = self.check_operation_safety(
            operation, 
            kwargs.get('target_branch'),
            kwargs.get('source_branch')
        )
        
        if not is_safe:
            return False, message
        
        # Si es segura, ejecutar la operación
        try:
            if operation == "merge":
                return self._execute_merge(kwargs.get('source_branch'), kwargs.get('target_branch'))
            elif operation == "push":
                return self._execute_push(kwargs.get('target_branch'))
            else:
                return False, f"Operación {operation} no implementada aún"
                
        except Exception as e:
            logger.error(f"Error ejecutando operación {operation}: {e}")
            return False, f"Error ejecutando operación: {e}"
    
    def _execute_merge(self, source_branch: str, target_branch: str) -> Tuple[bool, str]:
        """Ejecuta un merge de forma segura."""
        try:
            success, output = self.watcher.execute_git_command(
                f"git merge {source_branch}"
            )
            
            if success:
                return True, f"Merge exitoso: {source_branch} -> {target_branch}"
            else:
                return False, f"Error en merge: {output}"
                
        except Exception as e:
            return False, f"Error ejecutando merge: {e}"
    
    def _execute_push(self, target_branch: str) -> Tuple[bool, str]:
        """Ejecuta un push de forma segura."""
        try:
            success, output = self.watcher.execute_git_command(
                f"git push origin {target_branch}"
            )
            
            if success:
                return True, f"Push exitoso a {target_branch}"
            else:
                return False, f"Error en push: {output}"
                
        except Exception as e:
            return False, f"Error ejecutando push: {e}"


# Funciones de conveniencia para integración con Cursor
def check_git_operation_safety(operation: str, **kwargs) -> Tuple[bool, str, List[str]]:
    """
    Función de conveniencia para verificar seguridad de operaciones Git.
    
    Args:
        operation: Tipo de operación
        **kwargs: Argumentos adicionales
        
    Returns:
        Tuple[bool, str, List[str]]: (es_segura, mensaje, archivos_críticos)
    """
    blocking_logic = GitOpsBlockingLogic()
    return blocking_logic.check_operation_safety(operation, **kwargs)


def validate_critical_operation(operation: str, user_response: str, **kwargs) -> bool:
    """
    Función de conveniencia para validar confirmaciones del usuario.
    
    Args:
        operation: Tipo de operación
        user_response: Respuesta del usuario
        **kwargs: Argumentos adicionales
        
    Returns:
        bool: True si la confirmación es válida
    """
    blocking_logic = GitOpsBlockingLogic()
    return blocking_logic.validate_user_confirmation(user_response, operation, **kwargs)


# Ejemplo de uso para integración con Cursor
def example_cursor_integration():
    """
    Ejemplo de cómo integrar esta lógica en el Agente Principal de Cursor.
    """
    print("=== EJEMPLO DE INTEGRACIÓN CON CURSOR ===")
    
    # Simular verificación de merge
    is_safe, message, critical_files = check_git_operation_safety(
        "merge", 
        target_branch="main", 
        source_branch="feature/new-strategy"
    )
    
    print(f"Merge seguro: {is_safe}")
    print(f"Mensaje: {message}")
    print(f"Archivos críticos: {critical_files}")
    
    if not is_safe:
        print("\n⚠️ OPERACIÓN BLOQUEADA - REQUIERE CONFIRMACIÓN DEL USUARIO")
        print("El Agente Principal debe mostrar este mensaje al usuario y esperar confirmación.")
        
        # Simular confirmación del usuario
        user_confirmation = "CONFIRMO MERGE CRÍTICO"
        is_valid = validate_critical_operation("merge", user_confirmation)
        print(f"Confirmación válida: {is_valid}")


if __name__ == "__main__":
    example_cursor_integration()
