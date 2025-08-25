# Configuração do Gunicorn para produção
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 2
timeout = 120
graceful_timeout = 30

# Logging
accesslog = "/var/log/netplay/access.log"
errorlog = "/var/log/netplay/error.log"
loglevel = "info"

# Security
user = "www-data"
group = "www-data"

# Performance
worker_tmp_dir = "/dev/shm"