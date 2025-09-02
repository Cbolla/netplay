#!/usr/bin/env python3
"""
Netplay RPA - Sistema de Auto-Atualização
Monitora mudanças no código e reinicia automaticamente o servidor
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil

class CodeChangeHandler(FileSystemEventHandler):
    """Handler para detectar mudanças no código"""
    
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback
        self.last_restart = 0
        self.restart_delay = 2  # Aguarda 2 segundos antes de reiniciar
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Monitora apenas arquivos Python, HTML, CSS e JS
        if event.src_path.endswith(('.py', '.html', '.css', '.js', '.env')):
            current_time = time.time()
            
            # Evita reinicializações muito frequentes
            if current_time - self.last_restart > self.restart_delay:
                print(f"\n📝 Arquivo modificado: {event.src_path}")
                print("🔄 Reiniciando servidor...")
                self.last_restart = current_time
                self.restart_callback()

class NetplayAutoUpdater:
    """Sistema de auto-atualização do Netplay RPA"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.server_process = None
        self.observer = None
        self.running = True
        
        # Configurar handler de sinais
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handler para sinais de interrupção"""
        print("\n🛑 Parando sistema de auto-atualização...")
        self.running = False
        self.stop_server()
        if self.observer:
            self.observer.stop()
        sys.exit(0)
        
    def start_server(self):
        """Inicia o servidor FastAPI"""
        try:
            # Para o servidor anterior se estiver rodando
            self.stop_server()
            
            # Inicia novo servidor
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--reload"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            print(f"🚀 Servidor iniciado (PID: {self.server_process.pid})")
            print(f"🌐 Acesse: http://localhost:8000")
            print(f"🛡️ Admin: http://localhost:8000/admin")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False
            
    def stop_server(self):
        """Para o servidor atual"""
        if self.server_process:
            try:
                # Tenta parar graciosamente
                if os.name == 'nt':
                    # Windows
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.server_process.pid)], 
                                 capture_output=True)
                else:
                    # Linux/Mac
                    self.server_process.terminate()
                    self.server_process.wait(timeout=5)
                    
                print("⏹️ Servidor parado")
                
            except Exception as e:
                print(f"⚠️ Erro ao parar servidor: {e}")
                
            finally:
                self.server_process = None
                
        # Para processos uvicorn órfãos
        self.kill_orphan_processes()
        
    def kill_orphan_processes(self):
        """Mata processos uvicorn órfãos"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any('uvicorn' in str(arg) for arg in cmdline):
                            if any('main:app' in str(arg) for arg in cmdline):
                                print(f"🔪 Matando processo órfão: {proc.info['pid']}")
                                proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"⚠️ Erro ao limpar processos: {e}")
            
    def restart_server(self):
        """Reinicia o servidor"""
        print("\n🔄 Reiniciando servidor...")
        self.stop_server()
        time.sleep(1)
        self.start_server()
        print("✅ Servidor reiniciado com sucesso!\n")
        
    def setup_file_watcher(self):
        """Configura o monitoramento de arquivos"""
        event_handler = CodeChangeHandler(self.restart_server)
        self.observer = Observer()
        
        # Monitora diretório principal
        self.observer.schedule(event_handler, str(self.project_dir), recursive=False)
        
        # Monitora diretório frontend
        frontend_dir = self.project_dir / 'frontend'
        if frontend_dir.exists():
            self.observer.schedule(event_handler, str(frontend_dir), recursive=True)
            
        self.observer.start()
        print("👁️ Monitoramento de arquivos ativo")
        
    def show_status(self):
        """Mostra status do sistema"""
        print("\n" + "="*60)
        print("🛡️ NETPLAY RPA - SISTEMA DE AUTO-ATUALIZAÇÃO")
        print("="*60)
        print(f"📁 Diretório: {self.project_dir}")
        print(f"🔍 Monitorando: .py, .html, .css, .js, .env")
        print(f"🌐 URL Local: http://localhost:8000")
        print(f"🛡️ Admin: http://localhost:8000/admin")
        print(f"👥 Cliente: http://localhost:8000/client")
        print("="*60)
        print("📝 Qualquer alteração no código será aplicada automaticamente!")
        print("⏹️ Pressione Ctrl+C para parar")
        print("="*60 + "\n")
        
    def run(self):
        """Executa o sistema de auto-atualização"""
        try:
            self.show_status()
            
            # Inicia servidor
            if not self.start_server():
                return False
                
            # Configura monitoramento
            self.setup_file_watcher()
            
            # Loop principal
            while self.running:
                try:
                    time.sleep(1)
                    
                    # Verifica se servidor ainda está rodando
                    if self.server_process and self.server_process.poll() is not None:
                        print("⚠️ Servidor parou inesperadamente. Reiniciando...")
                        self.start_server()
                        
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            print(f"❌ Erro no sistema: {e}")
            
        finally:
            self.stop_server()
            if self.observer:
                self.observer.stop()
                self.observer.join()
                
        return True

def main():
    """Função principal"""
    print("🚀 Iniciando Netplay RPA Auto-Updater...")
    
    # Verifica dependências
    try:
        import watchdog
        import psutil
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("📦 Instalando dependências...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog", "psutil"])
        print("✅ Dependências instaladas!")
        
    # Inicia sistema
    updater = NetplayAutoUpdater()
    success = updater.run()
    
    if success:
        print("\n✅ Sistema de auto-atualização finalizado com sucesso!")
    else:
        print("\n❌ Sistema de auto-atualização finalizado com erro!")
        
if __name__ == "__main__":
    main()