
from config import Config


bind = '0.0.0.0:5000'
backlog = 2048

workers = Config.WORKERS
worker_class = 'gevent'
worker_connections = Config.WORKER_CONNECTIONS
timeout = 30
keepalive = 2

reload = Config.DEBUG
preload = Config.PRELOAD

errorlog = '-'
loglevel = Config.LOG_LEVEL
accesslog = None
