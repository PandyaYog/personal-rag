from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.process_document"]
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)