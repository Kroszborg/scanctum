import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import logging

from celery import Celery
from kombu import Connection
from kombu.common import maybe_declare

from app.config import settings

logger = logging.getLogger(__name__)

def _redis_url_with_ssl_verify(url: str) -> str:
    """Ensure ssl_cert_reqs=none for Upstash Redis compatibility."""
    if not url.strip().lower().startswith("rediss://"):
        return url
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    # Upstash requires ssl_cert_reqs=none for their proxy certificates
    q["ssl_cert_reqs"] = ["none"]
    new_query = urlencode(q, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


_broker = _redis_url_with_ssl_verify(settings.REDIS_URL)

celery_app = Celery(
    "scanctum",
    broker=_broker,
    backend=_broker,
    include=["app.tasks.scan_tasks", "app.tasks.report_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings for long-running scan tasks
    worker_prefetch_multiplier=1,  # Don't prefetch - one task at a time
    worker_concurrency=2,  # Number of concurrent tasks (matches docker-compose)
    worker_max_tasks_per_child=100,  # Recycle worker after 100 tasks (fresh DB connection)
    worker_send_task_events=True,  # Send events for Flower monitoring
    # Task settings
    task_acks_late=True,  # Acknowledge task after completion
    task_track_started=True,
    task_time_limit=5400,  # 90 min hard limit (full scans can take time)
    task_soft_time_limit=3600,  # 60 min soft limit
    task_reject_on_worker_lost=True,  # Re-queue on worker crash
    task_acks_on_failure_or_timeout=False,  # Don't ack on failure (allow retry)
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_backoff=60,  # Exponential backoff starting at 60s
    task_retry_backoff_max=600,  # Max 10 min between retries
    task_max_retries=3,  # Max 3 retries before giving up
    # Redis broker settings
    broker_transport_options={
        "visibility_timeout": 5400,  # Match task_time_limit
        "confirm_publish": True,
        "socket_connect_timeout": 5,
        "socket_keepalive": 1,
    },
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
    broker_connection_retry_delay=5,
    broker_heartbeat=30,  # Keep connection alive
    # Redis backend settings
    redis_backend_health_check_interval=30,
    result_extended=True,  # Store task state in Redis
    result_expires=3600,  # Expire results after 1 hour
)

# Prefork pool causes PermissionError on Windows (billiard semaphores). Use solo pool.
if sys.platform == "win32":
    celery_app.conf.worker_pool = "solo"
    celery_app.conf.worker_concurrency = 1  # Solo pool only supports 1 task

celery_app.autodiscover_tasks(["app.tasks"])
