"""
Controlador del bot de trading - maneja inicio/parada desde el dashboard
"""

import subprocess
import os
import signal
import psutil
import time
from datetime import datetime
import json

class BotController:
    """Controlador para manejar el bot de trading"""
    
    def __init__(self):
        self.bot_process = None
        self.status_file = "bot_status.json"
        self.pid_file = "bot.pid"
    
    def is_bot_running(self):
        """Verificar si el bot está ejecutándose"""
        try:
            # Verificar por PID
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Verificar si el proceso existe
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    if "python" in process.name().lower() and "main.py" in " ".join(process.cmdline()):
                        return True
            
            # Verificar por nombre de proceso
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
        except Exception as e:
            print(f"Error verificando estado del bot: {e}")
            return False
    
    def start_bot(self):
        """Iniciar el bot de trading"""
        try:
            if self.is_bot_running():
                return {"success": False, "message": "El bot ya está ejecutándose"}
            
            # Cambiar al directorio del proyecto
            project_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Comando para iniciar el bot
            cmd = [
                "venv\\Scripts\\python.exe",
                "main.py"
            ]
            
            # Iniciar el proceso
            self.bot_process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Guardar PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.bot_process.pid))
            
            # Actualizar estado
            self._update_status("running", "Bot iniciado desde dashboard")
            
            return {"success": True, "message": "Bot iniciado correctamente", "pid": self.bot_process.pid}
            
        except Exception as e:
            return {"success": False, "message": f"Error iniciando bot: {str(e)}"}
    
    def stop_bot(self):
        """Detener el bot de trading"""
        try:
            if not self.is_bot_running():
                return {"success": False, "message": "El bot no está ejecutándose"}
            
            # Encontrar y terminar el proceso
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            # Enviar señal de terminación
                            proc.terminate()
                            
                            # Esperar a que termine
                            try:
                                proc.wait(timeout=10)
                            except psutil.TimeoutExpired:
                                # Forzar terminación si no responde
                                proc.kill()
                            
                            # Limpiar archivos
                            if os.path.exists(self.pid_file):
                                os.remove(self.pid_file)
                            
                            # Actualizar estado
                            self._update_status("stopped", "Bot detenido desde dashboard")
                            
                            return {"success": True, "message": "Bot detenido correctamente"}
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"success": False, "message": "No se pudo encontrar el proceso del bot"}
            
        except Exception as e:
            return {"success": False, "message": f"Error deteniendo bot: {str(e)}"}
    
    def get_bot_status(self):
        """Obtener estado detallado del bot"""
        try:
            is_running = self.is_bot_running()
            
            status = {
                "running": is_running,
                "timestamp": datetime.now().isoformat(),
                "pid": None
            }
            
            if is_running:
                # Obtener PID del proceso
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                    try:
                        if proc.info['name'] and 'python' in proc.info['name'].lower():
                            cmdline = proc.info['cmdline']
                            if cmdline and any('main.py' in arg for arg in cmdline):
                                status["pid"] = proc.info['pid']
                                status["start_time"] = datetime.fromtimestamp(proc.info['create_time']).isoformat()
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            return status
            
        except Exception as e:
            return {"running": False, "error": str(e)}
    
    def _update_status(self, status, message):
        """Actualizar archivo de estado"""
        try:
            status_data = {
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            print(f"Error actualizando estado: {e}")

# Instancia global del controlador
bot_controller = BotController()




