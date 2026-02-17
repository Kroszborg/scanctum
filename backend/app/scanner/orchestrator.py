import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.result import Evidence, Vulnerability
from app.models.scan import Scan
from app.scanner.crawler import AsyncCrawler, CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import Finding
from app.scanner.modules.registry import ModuleRegistry
from app.scanner.rate_limiter import CircuitBreaker, PerDomainThrottle
from app.scanner.scope import ScopeValidator

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    """Orchestrates the scan pipeline: crawl → detect → score → persist."""

    def __init__(self, scan_id: str, db_session: Session):
        self.scan_id = uuid.UUID(scan_id)
        self.db = db_session
        self.scan: Scan | None = None

    def run(self) -> None:
        """Main entry point for running a scan (called from Celery)."""
        import asyncio
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            logger.exception(f"Detailed scan error: {e}")
            raise

    async def _run_async(self) -> None:
        self.scan = self.db.get(Scan, self.scan_id)
        if self.scan is None:
            logger.error(f"Scan {self.scan_id} not found")
            return

        try:
            self._update_status("crawling", 5)
            self.scan.started_at = datetime.now(timezone.utc)
            self.db.commit()

            # Determine scan parameters
            is_full = self.scan.scan_mode == "full"
            max_depth = settings.SCANNER_MAX_DEPTH_FULL if is_full else settings.SCANNER_MAX_DEPTH_QUICK
            max_pages = settings.SCANNER_MAX_PAGES_FULL if is_full else settings.SCANNER_MAX_PAGES_QUICK

            # Setup components
            throttle = PerDomainThrottle(delay=settings.SCANNER_REQUEST_DELAY)
            circuit_breaker = CircuitBreaker()
            http_client = HttpClient(
                throttle=throttle,
                circuit_breaker=circuit_breaker,
                custom_headers=(self.scan.config or {}).get("custom_headers"),
            )
            scope = ScopeValidator(
                self.scan.target_url,
                include_subdomains=(self.scan.config or {}).get("include_subdomains", False),
                exclude_patterns=(self.scan.config or {}).get("exclude_patterns"),
            )
            crawler = AsyncCrawler(
                http_client=http_client,
                scope=scope,
                max_depth=max_depth,
                max_pages=max_pages,
                concurrency=settings.SCANNER_CONCURRENCY,
            )

            # Phase 1: Crawl
            pages = await crawler.crawl(self.scan.target_url)
            self.scan.pages_found = len(pages)
            self._update_status("scanning", 30)

            # Phase 2: Run modules
            modules = ModuleRegistry.get_for_mode(self.scan.scan_mode)
            all_findings: list[Finding] = []

            for i, page in enumerate(pages):
                if self._is_cancelled():
                    return

                page_findings = await self._scan_page(page, modules, http_client)
                all_findings.extend(page_findings)

                self.scan.pages_scanned = i + 1
                progress = 30 + int((i + 1) / max(len(pages), 1) * 60)
                self._update_status("scanning", min(progress, 90))

            # Phase 3: Deduplicate and persist
            unique_findings = self._deduplicate(all_findings)
            self._persist_findings(unique_findings)
            self._update_status("completed", 100)
            self.scan.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            await http_client.close()

        except Exception as e:
            logger.exception(f"Scan {self.scan_id} failed: {e}")
            self.scan.status = "failed"
            self.scan.error_message = str(e)
            self.scan.completed_at = datetime.now(timezone.utc)
            self.db.commit()

    async def _scan_page(
        self, page: CrawledPage, modules: list, http_client: HttpClient
    ) -> list[Finding]:
        findings: list[Finding] = []

        for module in modules:
            try:
                # Passive detection
                passive_findings = await module.detect_async(page)
                findings.extend(passive_findings)

                # Active testing
                if module.is_active:
                    active_findings = await module.active_test_async(page, http_client)
                    findings.extend(active_findings)
            except Exception as e:
                logger.warning(f"Module {module.name} error on {page.url}: {e}")

        return findings

    def _deduplicate(self, findings: list[Finding]) -> list[Finding]:
        seen: set[str] = set()
        unique: list[Finding] = []
        for f in findings:
            key = f"{f.module_name}:{f.vuln_type}:{f.affected_url}:{f.affected_parameter or ''}"
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _persist_findings(self, findings: list[Finding]) -> None:
        for f in findings:
            vuln = Vulnerability(
                scan_id=self.scan_id,
                module_name=f.module_name,
                vuln_type=f.vuln_type,
                severity=f.severity,
                cvss_score=f.cvss_score,
                cvss_vector=f.cvss_vector,
                owasp_category=f.owasp_category,
                cwe_id=f.cwe_id,
                affected_url=f.affected_url,
                affected_parameter=f.affected_parameter,
                description=f.description,
                remediation=f.remediation,
                confidence=f.confidence,
            )
            self.db.add(vuln)
            self.db.flush()

            for idx, ev in enumerate(f.evidence):
                evidence = Evidence(
                    vulnerability_id=vuln.id,
                    evidence_type=ev.get("type", "log"),
                    title=ev.get("title", ""),
                    content=ev.get("content", ""),
                    order_index=idx,
                )
                self.db.add(evidence)

        self.db.commit()

    def _update_status(self, status: str, progress: int) -> None:
        self.scan.status = status
        self.scan.progress_percent = progress
        self.db.commit()

    def _is_cancelled(self) -> bool:
        self.db.refresh(self.scan)
        return self.scan.status == "cancelled"
