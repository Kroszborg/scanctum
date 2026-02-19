"""Celery task for asynchronous PDF report generation."""
import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.report_tasks.generate_pdf")
def generate_pdf(self, scan_id: str) -> dict:
    """Generate a PDF report for a completed scan asynchronously.

    This task is used for large or slow reports.  For most scans the API
    handler calls report_service.generate_pdf_report() directly (synchronous).
    This Celery task is available for long-running reports or when you want
    to pre-generate and cache the PDF.
    """
    logger.info(f"Generating PDF report for scan {scan_id}")
    from app.db.session import get_sync_session

    db = get_sync_session()
    try:
        # Use sync ORM to load scan + vulnerabilities
        from app.models.scan import Scan
        from app.models.result import Vulnerability
        from sqlalchemy.orm import selectinload

        scan = (
            db.query(Scan)
            .options(selectinload(Scan.vulnerabilities))
            .filter(Scan.id == scan_id)
            .first()
        )
        if scan is None:
            logger.error(f"Scan {scan_id} not found")
            return {"status": "failed", "error": "Scan not found"}

        if scan.status != "completed":
            logger.warning(f"Scan {scan_id} is not completed (status={scan.status})")
            return {"status": "skipped", "reason": f"scan status is {scan.status}"}

        # Build findings list for the template
        findings = [
            {
                "vuln_type": v.vuln_type,
                "severity": v.severity,
                "cvss_score": float(v.cvss_score),
                "cvss_vector": v.cvss_vector,
                "owasp_category": v.owasp_category,
                "cwe_id": v.cwe_id,
                "affected_url": v.affected_url,
                "affected_parameter": v.affected_parameter,
                "description": v.description,
                "remediation": v.remediation,
                "confidence": v.confidence,
                "module_name": v.module_name,
            }
            for v in sorted(scan.vulnerabilities, key=lambda v: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(v.severity, 5),
            ))
        ]

        # Render PDF via Jinja2 + xhtml2pdf
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        from pathlib import Path
        import datetime

        template_dir = Path(__file__).resolve().parent.parent / "templates" / "reports"
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        tmpl = env.get_template("report.html")

        severity_counts = {s: 0 for s in ("critical", "high", "medium", "low", "info")}
        for f in findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

        html = tmpl.render(
            scan=scan,
            findings=findings,
            severity_counts=severity_counts,
            generated_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        )

        try:
            from xhtml2pdf import pisa
            import io
            buf = io.BytesIO()
            pisa.CreatePDF(html, dest=buf)
            pdf_bytes = buf.getvalue()
            logger.info(f"PDF generated for scan {scan_id}: {len(pdf_bytes)} bytes")
        except Exception as e:
            logger.warning(f"xhtml2pdf failed: {e} — falling back to HTML bytes")
            pdf_bytes = html.encode()

        return {
            "status": "completed",
            "scan_id": scan_id,
            "size_bytes": len(pdf_bytes),
        }
    except Exception as e:
        logger.exception(f"PDF generation failed for scan {scan_id}: {e}")
        return {"status": "failed", "scan_id": scan_id, "error": str(e)}
    finally:
        db.close()
