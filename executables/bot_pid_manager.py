#!/usr/bin/env python3
"""
Bot PID Manager - Sistema robusto de control de procesos
Maneja el tracking, inicio y detención del bot de trading
"""

import os
import sys
import json
import time
import psutil
import subprocess
from pathlib import Path
from datetime import datetime

class BotPIDManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.pid_file = self.project_root / "executables" / "bot.pid"
        self.status_file = self.project_root / "executables" / "bot_status.json"
        self.log_file = self.project_root / "backtrader_engine" / "logs" / "pid_manager.log"
        
    def log(self, message: str):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        # Escribir al archivo de log
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + "\n")
        except:
            pass
    
    def get_bot_processes(self):
        """Obtiene todos los procesos del bot"""
        bot_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['name'] == 'python.exe':
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'paper_trading_main.py' in cmdline:
                        bot_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline,
                            'create_time': proc.info['create_time']
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return bot_processes
    
    def save_pid(self, pid: int):
        """Guarda el PID del bot"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
            
            # Guardar estado completo
            status = {
                'pid': pid,
                'start_time': datetime.now().isoformat(),
                'status': 'running',
                'last_check': datetime.now().isoformat()
            }
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            self.log(f"PID {pid} guardado correctamente")
            return True
        except Exception as e:
            self.log(f"Error guardando PID: {e}")
            return False
    
    def get_saved_pid(self):
        """Obtiene el PID guardado"""
        try:
            if self.pid_file.exists():
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except:
            pass
        return None
    
    def is_bot_running(self):
        """Verifica si el bot está ejecutándose"""
        saved_pid = self.get_saved_pid()
        if not saved_pid:
            return False, None
        
        try:
            proc = psutil.Process(saved_pid)
            if proc.is_running() and 'paper_trading_main.py' in ' '.join(proc.cmdline()):
                return True, saved_pid
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        return False, None
    
    def start_bot(self):
        """Inicia el bot y guarda el PID"""
        self.log("=== INICIANDO BOT ===")
        
        # Verificar si ya está ejecutándose
        is_running, pid = self.is_bot_running()
        if is_running:
            self.log(f"Bot ya está ejecutándose con PID {pid}")
            return True, pid
        
        # Limpiar procesos colgados
        self.cleanup_dead_processes()
        
        # Cambiar al directorio del bot
        bot_dir = self.project_root / "backtrader_engine"
        os.chdir(bot_dir)
        
        # Iniciar el bot
        try:
            self.log("Ejecutando comando de inicio...")
            process = subprocess.Popen([
                sys.executable, 
                "paper_trading_main.py", 
                "--config", 
                "configs/bybit_x_config.json"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Esperar un poco para que se inicie
            time.sleep(3)
            
            # Verificar que el proceso sigue ejecutándose
            if process.poll() is None:
                self.save_pid(process.pid)
                self.log(f"Bot iniciado correctamente con PID {process.pid}")
                return True, process.pid
            else:
                stdout, stderr = process.communicate()
                self.log(f"Error iniciando bot: {stderr.decode()}")
                return False, None
                
        except Exception as e:
            self.log(f"Excepción iniciando bot: {e}")
            return False, None
    
    def stop_bot(self, force=False):
        """Detiene el bot"""
        self.log("=== DETENIENDO BOT ===")
        
        # Método 1: Usar PID guardado
        is_running, saved_pid = self.is_bot_running()
        if is_running:
            self.log(f"Deteniendo bot con PID {saved_pid}")
            try:
                proc = psutil.Process(saved_pid)
                if force:
                    proc.kill()
                    self.log(f"Bot terminado forzadamente (PID {saved_pid})")
                else:
                    proc.terminate()
                    # Esperar terminación graceful
                    try:
                        proc.wait(timeout=10)
                        self.log(f"Bot detenido gracefulmente (PID {saved_pid})")
                    except psutil.TimeoutExpired:
                        proc.kill()
                        self.log(f"Bot terminado forzadamente por timeout (PID {saved_pid})")
                
                self.cleanup_pid_files()
                return True
            except Exception as e:
                self.log(f"Error deteniendo bot con PID guardado: {e}")
        
        # Método 2: Buscar por nombre de proceso
        self.log("Buscando procesos del bot por nombre...")
        bot_processes = self.get_bot_processes()
        if bot_processes:
            for proc_info in bot_processes:
                try:
                    proc = psutil.Process(proc_info['pid'])
                    if force:
                        proc.kill()
                        self.log(f"Proceso {proc_info['pid']} terminado forzadamente")
                    else:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                            self.log(f"Proceso {proc_info['pid']} detenido gracefulmente")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            self.log(f"Proceso {proc_info['pid']} terminado forzadamente")
                except Exception as e:
                    self.log(f"Error deteniendo proceso {proc_info['pid']}: {e}")
            
            self.cleanup_pid_files()
            return True
        
        # Método 3: Terminar todos los procesos Python (último recurso)
        if force:
            self.log("Método de emergencia: terminando todos los procesos Python")
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] == 'python.exe':
                        proc.kill()
                        self.log(f"Proceso Python {proc.info['pid']} terminado")
                except:
                    pass
            
            self.cleanup_pid_files()
            return True
        
        self.log("No se encontraron procesos del bot para detener")
        return False
    
    def cleanup_dead_processes(self):
        """Limpia procesos muertos y archivos PID obsoletos"""
        self.log("Limpiando procesos muertos...")
        
        # Verificar si el PID guardado corresponde a un proceso muerto
        saved_pid = self.get_saved_pid()
        if saved_pid:
            try:
                proc = psutil.Process(saved_pid)
                if not proc.is_running():
                    self.log(f"PID {saved_pid} corresponde a un proceso muerto, limpiando...")
                    self.cleanup_pid_files()
            except psutil.NoSuchProcess:
                self.log(f"PID {saved_pid} no existe, limpiando...")
                self.cleanup_pid_files()
    
    def cleanup_pid_files(self):
        """Limpia archivos de PID y estado"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            if self.status_file.exists():
                self.status_file.unlink()
            self.log("Archivos de PID limpiados")
        except Exception as e:
            self.log(f"Error limpiando archivos PID: {e}")
    
    def get_status(self):
        """Obtiene el estado actual del bot"""
        is_running, pid = self.is_bot_running()
        bot_processes = self.get_bot_processes()
        
        status = {
            'is_running': is_running,
            'pid': pid,
            'total_processes': len(bot_processes),
            'processes': bot_processes,
            'timestamp': datetime.now().isoformat()
        }
        
        return status

def main():
    if len(sys.argv) < 2:
        print("Uso: python bot_pid_manager.py <comando> [opciones]")
        print("Comandos: start, stop, status, force-stop")
        sys.exit(1)
    
    command = sys.argv[1]
    project_root = Path(__file__).parent.parent
    
    manager = BotPIDManager(project_root)
    
    if command == "start":
        success, pid = manager.start_bot()
        if success:
            print(f"SUCCESS: Bot iniciado con PID {pid}")
            sys.exit(0)
        else:
            print("ERROR: No se pudo iniciar el bot")
            sys.exit(1)
    
    elif command == "stop":
        success = manager.stop_bot(force=False)
        if success:
            print("SUCCESS: Bot detenido correctamente")
            sys.exit(0)
        else:
            print("ERROR: No se pudo detener el bot")
            sys.exit(1)
    
    elif command == "force-stop":
        success = manager.stop_bot(force=True)
        if success:
            print("SUCCESS: Bot detenido forzadamente")
            sys.exit(0)
        else:
            print("ERROR: No se pudo detener el bot")
            sys.exit(1)
    
    elif command == "status":
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    else:
        print(f"Comando desconocido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
