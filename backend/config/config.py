import os
import subprocess


def get_tag():
    result = subprocess.run(["git", "describe", "--abbrev=0", "--tags"], stdout=subprocess.PIPE)
    return str(result.stdout.decode("utf-8")).strip()


class Config:

    NAME = os.getenv("NAME", "COCO Annotator")
    VERSION = get_tag()

    ### File Watcher
    FILE_WATCHER = os.getenv("FILE_WATCHER", False)
    IGNORE_DIRECTORIES = ["_thumbnail", "_settings"]

    # Flask/Gunicorn
    #
    #   LOG_LEVEL - The granularity of log output
    #
    #       A string of "debug", "info", "warning", "error", "critical"
    #
    #   WORKER_CONNECTIONS - limits the maximum number of simultaneous
    #       clients that a single process can handle.
    #
    #       A positive integer generally set to around 1000.
    #
    #   WORKER_TIMEOUT - If a worker does not notify the master process
    #       in this number of seconds it is killed and a new worker is
    #       spawned to replace it.
    #
    SWAGGER_UI_JSONEDITOR = True
    DEBUG = os.getenv("DEBUG", 'false').lower() == 'true'
    PRELOAD = False

    MAX_CONTENT_LENGTH = os.getenv("MAX_CONTENT_LENGTH", 1 * 1024 * 1024 * 1024)  # 1GB
    MONGODB_HOST = os.getenv("MONGODB_HOST", "mongodb://database/flask")
    SECRET_KEY = os.getenv("SECRET_KEY", "<--- CHANGE THIS KEY --->")

    LOG_LEVEL = os.getenv("LOG_LEVEL", 'info')
    WORKERS = 1
    WORKER_CONNECTIONS = 1000

    TESTING = os.getenv("TESTING", False)

    ### Workers
    CELERY_BROKER_URL = os.getenv("BROKER_URL", "amqp://user:password@messageq:5672//")
    CELERY_RESULT_BACKEND = os.getenv("BROKER_RESULT_BACKEND", "mongodb://database/flask")

    ### Dataset Options
    DATASET_DIRECTORY = os.getenv("DATASET_DIRECTORY", "/datasets/")
    INITIALIZE_FROM_FILE = os.getenv("INITIALIZE_FROM_FILE")

    ### User Options
    LOGIN_DISABLED = os.getenv("LOGIN_DISABLED", False)
    ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "True").lower() == "true"

    ### Models
    MASK_RCNN_FILE = os.getenv("MASK_RCNN_FILE", "")
    MASK_RCNN_CLASSES = os.getenv("MASK_RCNN_CLASSES", "BG")

    DEXTR_FILE = os.getenv("DEXTR_FILE", "/models/dextr_pascal-sbd.h5")

    CORS_ALLOWED_ORIGINS = [
        origin for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").replace(" ", "").split(",")
        if len(origin) > 0
    ]


__all__ = ["Config"]
