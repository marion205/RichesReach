# Gunicorn configuration for production (optimized for FastAPI/Uvicorn)
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - use UvicornWorker for async FastAPI
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count()))
worker_class = "uvicorn.workers.UvicornWorker"
threads = 1  # Uvicorn handles async, no threads needed
timeout = 60
graceful_timeout = 30
keepalive = 75  # Longer keepalive for better HTTP/2 support

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'richesreach-backend'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if using HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Preload app - disable if ONNX/ORT models aren't fork-safe
preload_app = False

# Uvicorn tuning via environment
raw_env = [
    "UVICORN_HTTP=httptools",
    "UVICORN_LOOP=uvloop",
]

# Worker timeout for health checks
worker_tmp_dir = '/dev/shm'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
