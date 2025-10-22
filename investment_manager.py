"""
Investment Dashboard Manager
Módulo para gestionar el Investment Dashboard desde el bot de trading
"""

import subprocess
import os
import time
import requests
from typing import Dict, Optional, Tuple
import psutil
from datetime import datetime


class InvestmentDashboardManager:
    """Gestor del Investment Dashboard"""
    
    def __init__(self):
        self.project_dir = "/home/alex/proyectos/investment-dashboard"
        self.log_dir = f"{self.project_dir}/logs"
        self.pid_file = f"{self.log_dir}/investment_dashboard.pid"
        self.script_dir = f"{self.project_dir}/scripts"
        self.backend_port = 8000
        self.frontend_port = 3000
        
        # Crear directorio de logs si no existe
        os.makedirs(self.log_dir, exist_ok=True)
    
    def is_process_running(self, pid: int) -> bool:
        """Verifica si un proceso está corriendo"""
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_pids(self) -> Dict[str, Optional[int]]:
        """Obtiene los PIDs de backend y frontend"""
        pids = {"backend": None, "frontend": None}
        
        # Intentar leer del archivo PID
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    for line in f:
                        if ':' in line:
                            service, pid = line.strip().split(':')
                            pids[service] = int(pid)
            except Exception:
                pass
        
        # Si no hay archivo PID, buscar por puerto
        if not pids["backend"]:
            pids["backend"] = self._get_pid_by_port(self.backend_port)
        if not pids["frontend"]:
            pids["frontend"] = self._get_pid_by_port(self.frontend_port)
        
        return pids
    
    def _get_pid_by_port(self, port: int) -> Optional[int]:
        """Obtiene el PID de un proceso escuchando en un puerto"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return conn.pid
        except (psutil.AccessDenied, AttributeError):
            pass
        return None
    
    def get_status(self) -> Dict[str, any]:
        """Obtiene el estado completo del Investment Dashboard"""
        pids = self.get_pids()
        
        backend_running = False
        frontend_running = False
        backend_info = {}
        frontend_info = {}
        
        # Verificar Backend
        if pids["backend"] and self.is_process_running(pids["backend"]):
            backend_running = True
            try:
                proc = psutil.Process(pids["backend"])
                backend_info = {
                    "pid": pids["backend"],
                    "status": "running",
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_mb": proc.memory_info().rss / 1024 / 1024,
                    "create_time": datetime.fromtimestamp(proc.create_time()),
                    "uptime": str(datetime.now() - datetime.fromtimestamp(proc.create_time())).split('.')[0]
                }
            except Exception as e:
                backend_info = {"status": "error", "error": str(e)}
        else:
            backend_info = {"status": "stopped"}
        
        # Verificar Frontend
        if pids["frontend"] and self.is_process_running(pids["frontend"]):
            frontend_running = True
            try:
                proc = psutil.Process(pids["frontend"])
                frontend_info = {
                    "pid": pids["frontend"],
                    "status": "running",
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_mb": proc.memory_info().rss / 1024 / 1024,
                    "create_time": datetime.fromtimestamp(proc.create_time()),
                    "uptime": str(datetime.now() - datetime.fromtimestamp(proc.create_time())).split('.')[0]
                }
            except Exception as e:
                frontend_info = {"status": "error", "error": str(e)}
        else:
            frontend_info = {"status": "stopped"}
        
        # Verificar conectividad
        backend_responding = self._check_endpoint(f"http://127.0.0.1:{self.backend_port}")
        frontend_responding = self._check_endpoint(f"http://127.0.0.1:{self.frontend_port}")
        
        return {
            "overall_status": "running" if (backend_running and frontend_running) else "partial" if (backend_running or frontend_running) else "stopped",
            "backend": {
                **backend_info,
                "port": self.backend_port,
                "responding": backend_responding,
                "url": f"http://127.0.0.1:{self.backend_port}"
            },
            "frontend": {
                **frontend_info,
                "port": self.frontend_port,
                "responding": frontend_responding,
                "url": f"http://127.0.0.1:{self.frontend_port}"
            },
            "logs": {
                "backend": f"{self.log_dir}/backend.log",
                "frontend": f"{self.log_dir}/frontend.log"
            }
        }
    
    def _check_endpoint(self, url: str, timeout: int = 2) -> bool:
        """Verifica si un endpoint está respondiendo"""
        try:
            # Para backend FastAPI, intentar /docs (Swagger siempre está disponible)
            if ":8000" in url:
                test_url = f"{url}/docs"
            else:
                test_url = url
            
            response = requests.get(test_url, timeout=timeout, allow_redirects=True)
            # Aceptar 200, 404, o 3xx (redirects)
            return response.status_code < 500
        except:
            return False
    
    def start(self) -> Tuple[bool, str]:
        """Inicia el Investment Dashboard"""
        try:
            # Verificar si ya está corriendo
            status = self.get_status()
            if status["overall_status"] == "running":
                return False, "Investment Dashboard ya está corriendo"
            
            # Ejecutar script de inicio
            script_path = f"{self.script_dir}/start_investment_dashboard.sh"
            
            if not os.path.exists(script_path):
                return False, f"Script de inicio no encontrado: {script_path}"
            
            # Iniciar en background sin esperar (el script ya maneja nohup)
            process = subprocess.Popen(
                ["/bin/bash", script_path],
                cwd=self.script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Esperar solo 2 segundos y verificar que el proceso empezó
            time.sleep(2)
            
            # No esperar a que termine el script, solo verificar que inició
            return True, "Investment Dashboard iniciando... Espera 10-15 segundos y refresca"
                
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def stop(self) -> Tuple[bool, str]:
        """Detiene el Investment Dashboard"""
        try:
            # Verificar si está corriendo
            status = self.get_status()
            if status["overall_status"] == "stopped":
                return False, "Investment Dashboard ya está detenido"
            
            # Ejecutar script de detención
            script_path = f"{self.script_dir}/stop_investment_dashboard.sh"
            
            if not os.path.exists(script_path):
                # Si no existe el script, intentar detener manualmente
                return self._manual_stop()
            
            result = subprocess.run(
                [script_path],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Esperar un poco y verificar
                time.sleep(3)
                status = self.get_status()
                if status["overall_status"] == "stopped":
                    return True, "Investment Dashboard detenido correctamente"
                else:
                    return False, f"Dashboard parcialmente detenido. Estado: {status['overall_status']}"
            else:
                return False, f"Error al detener: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout al detener el dashboard (>30s)"
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def _manual_stop(self) -> Tuple[bool, str]:
        """Detiene el dashboard manualmente matando los procesos"""
        try:
            pids = self.get_pids()
            stopped = []
            errors = []
            
            for service, pid in pids.items():
                if pid and self.is_process_running(pid):
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=10)
                        stopped.append(service)
                    except psutil.TimeoutExpired:
                        proc.kill()
                        stopped.append(f"{service} (forzado)")
                    except Exception as e:
                        errors.append(f"{service}: {str(e)}")
            
            # Limpiar archivo PID
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            if stopped and not errors:
                return True, f"Servicios detenidos: {', '.join(stopped)}"
            elif stopped and errors:
                return True, f"Parcialmente detenido. Detenidos: {', '.join(stopped)}. Errores: {', '.join(errors)}"
            else:
                return False, f"No se pudo detener. Errores: {', '.join(errors)}"
                
        except Exception as e:
            return False, f"Error en detención manual: {str(e)}"
    
    def restart(self) -> Tuple[bool, str]:
        """Reinicia el Investment Dashboard"""
        success, msg = self.stop()
        if not success and "ya está detenido" not in msg:
            return False, f"Error al detener: {msg}"
        
        time.sleep(2)
        
        return self.start()
    
    def get_logs(self, service: str = "backend", lines: int = 50) -> str:
        """Obtiene las últimas líneas de logs"""
        log_file = f"{self.log_dir}/{service}.log"
        
        if not os.path.exists(log_file):
            return f"Archivo de log no encontrado: {log_file}"
        
        try:
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception as e:
            return f"Error al leer logs: {str(e)}"


# Instancia global para usar en el dashboard
investment_manager = InvestmentDashboardManager()


if __name__ == "__main__":
    # Test del módulo
    manager = InvestmentDashboardManager()
    
    print("=== Investment Dashboard Manager Test ===\n")
    
    # Obtener estado
    print("Estado actual:")
    status = manager.get_status()
    print(f"  Overall: {status['overall_status']}")
    print(f"  Backend: {status['backend']['status']}")
    print(f"  Frontend: {status['frontend']['status']}")
    print()
