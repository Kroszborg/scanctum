from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient


@dataclass
class Finding:
    module_name: str
    vuln_type: str
    severity: str
    cvss_score: float
    cvss_vector: str
    owasp_category: str
    cwe_id: str
    affected_url: str
    affected_parameter: str | None
    description: str
    remediation: str
    confidence: str = "firm"
    evidence: list[dict] = field(default_factory=list)


class BaseModule(ABC):
    """Abstract base for all scanner modules."""

    name: str = ""
    description: str = ""
    scan_modes: list[str] = ["quick", "full"]  # Which scan modes include this module
    is_active: bool = False  # Whether this module sends crafted requests

    def detect(self, page: CrawledPage) -> list[Finding]:
        """Passive analysis of already-fetched page. Override in passive modules."""
        return []

    def active_test(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        """Send crafted requests for active testing. Override in active modules."""
        return []

    async def detect_async(self, page: CrawledPage) -> list[Finding]:
        """Async wrapper for detect."""
        return self.detect(page)

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        """Async wrapper for active_test."""
        return self.active_test(page, http_client)
