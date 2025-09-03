# Configuração do Gunicorn para Produção
# Sistema Netplay

import os
import multiprocessing

# Configurações básicas
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = int(os.getenv('MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', '100'))
timeout = int(os.getenv('TIMEOUT', '30'))
keepalive = int(os.getenv('KEEP_ALIVE', '5'))

# Configurações de processo
user = "netplay"
group = "netplay"
tmp_upload_dir = None
preload_app = True

# Logs
accesslog = "/var/log/netplay/access.log"
errorlog = "/var/log/netplay/error.log"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de performance
worker_tmp_dir = "/dev/shm"

# Hooks
def on_starting(server):
    server.log.info("Sistema Netplay iniciando...")

def on_reload(server):
    server.log.info("Sistema Netplay recarregando...")

def worker_int(worker):
    worker.log.info("Worker recebeu INT ou QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")

def on_exit(server):
    server.log.info("Sistema Netplay finalizando...")

# Configurações SSL (descomente se necessário)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ssl_version = 2
# cert_reqs = 0
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None