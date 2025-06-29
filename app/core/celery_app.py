from celery import Celery
from app.core.config import settings

broker_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
backend_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"

celery_app = Celery(
    "tasks",
    broker=broker_url,
    backend=backend_url,
    include=["app.tasks.process_document"]
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)