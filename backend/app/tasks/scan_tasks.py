import logging

from app.tasks.celery_app import celery_app
from app.db.session import get_sync_session
from app.scanner.orchestrator import ScanOrchestrator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.scan_tasks.run_scan")
def run_scan(self, scan_id: str) -> dict:
    """Celery task to execute a scan."""
    logger.info(f"Starting scan {scan_id}")
    db = get_sync_session()
    try:
        orchestrator = ScanOrchestrator(scan_id, db)
        orchestrator.run()
        return {"status": "completed", "scan_id": scan_id}
    except Exception as e:
        logger.exception(f"Scan {scan_id} failed: {e}")
        return {"status": "failed", "scan_id": scan_id, "error": str(e)}
    finally:
        db.close()
