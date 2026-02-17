import sys

from celery import Celery

from app.config import settings

celery_app = Celery(
    "scanctum",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.scan_tasks", "app.tasks.report_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Long-running tasks
    task_acks_late=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=2700,  # 45 min soft limit
)

# Prefork pool causes PermissionError on Windows (billiard semaphores). Use solo pool.
if sys.platform == "win32":
    celery_app.conf.worker_pool = "solo"

celery_app.autodiscover_tasks(["app.tasks"])
