import sys
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from celery import Celery

from app.config import settings


def _redis_url_with_ssl_verify(url: str) -> str:
    """Append ssl_cert_reqs=CERT_REQUIRED so Kombu validates Redis TLS (removes CERT_NONE warning)."""
    if not url.strip().lower().startswith("rediss://"):
        return url
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    q["ssl_cert_reqs"] = ["CERT_REQUIRED"]
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
