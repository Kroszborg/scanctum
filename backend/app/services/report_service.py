import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.result import Vulnerability
from app.models.scan import Scan
from app.schemas.result import VulnerabilityResponse
from app.scanner.scoring.severity import OWASP_TOP_10

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "reports"


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_scan_with_vulns(self, scan_id: uuid.UUID, user_id: uuid.UUID):
        result = await self.db.execute(
            select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
        )
        scan = result.scalar_one_or_none()
        if scan is None:
            raise NotFoundError("Scan not found")

        vulns_result = await self.db.execute(
            select(Vulnerability)
            .where(Vulnerability.scan_id == scan_id)
            .options(selectinload(Vulnerability.evidence))
            .order_by(Vulnerability.cvss_score.desc())
        )
        vulns = list(vulns_result.scalars().all())
        return scan, vulns

    async def generate_json_report(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        scan, vulns = await self._get_scan_with_vulns(scan_id, user_id)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for v in vulns:
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1

        return {
            "report": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "scanner": "Scanctum v0.1",
            },
            "scan": {
                "id": str(scan.id),
                "target_url": scan.target_url,
                "scan_mode": scan.scan_mode,
                "status": scan.status,
                "started_at": scan.started_at.isoformat() if scan.started_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "pages_found": scan.pages_found,
                "pages_scanned": scan.pages_scanned,
            },
            "summary": {
                "total_vulnerabilities": len(vulns),
                "severity_distribution": severity_counts,
                "risk_level": self._risk_level(severity_counts),
            },
            "vulnerabilities": [
                VulnerabilityResponse.model_validate(v).model_dump(mode="json")
                for v in vulns
            ],
        }

    async def generate_pdf_report(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> bytes:

        
        scan, vulns = await self._get_scan_with_vulns(scan_id, user_id)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        owasp_counts: dict[str, int] = {}
        for v in vulns:
            severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1
            owasp_counts[v.owasp_category] = owasp_counts.get(v.owasp_category, 0) + 1

        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template("report.html")

        html_content = template.render(
            scan=scan,
            vulnerabilities=vulns,
            severity_counts=severity_counts,
            owasp_counts=owasp_counts,
            owasp_top_10=OWASP_TOP_10,
            risk_level=self._risk_level(severity_counts),
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            total_vulns=len(vulns),
        )

        # Try WeasyPrint first (better quality), fallback to xhtml2pdf if unavailable
        try:
            import warnings
            # Suppress WeasyPrint import warnings about missing system libraries
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except (ImportError, OSError, Exception) as e:
            # Fallback for Windows/environments without GTK/system libs: use xhtml2pdf
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"WeasyPrint unavailable ({type(e).__name__}), using xhtml2pdf fallback")
            from xhtml2pdf import pisa
            from io import BytesIO
            
            result = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=result
            )
            if pisa_status.err:
                raise Exception("PDF generation error (xhtml2pdf fallback failed)")
            pdf_bytes = result.getvalue()

        return pdf_bytes

    @staticmethod
    def _risk_level(counts: dict) -> str:
        if counts.get("critical", 0) > 0:
            return "Critical"
        if counts.get("high", 0) > 0:
            return "High"
        if counts.get("medium", 0) > 0:
            return "Medium"
        if counts.get("low", 0) > 0:
            return "Low"
        return "Informational"
