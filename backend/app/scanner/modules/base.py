from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import enum

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient


class FindingCategory(enum.Enum):
    """Category of vulnerability for proper prioritization."""
    EXPLOITABLE = "exploitable"          # Confirmed exploitation possible
    MISCONFIGURATION = "misconfiguration"  # Security hardening recommended
    INFORMATIONAL = "informational"        # Awareness only, not a vulnerability


class FindingSeverity(enum.Enum):
    """Severity levels aligned with CVSS."""
    CRITICAL = "critical"  # CVSS 9.0-10.0
    HIGH = "high"          # CVSS 7.0-8.9
    MEDIUM = "medium"      # CVSS 4.0-6.9
    LOW = "low"            # CVSS 0.1-3.9
    INFO = "info"          # CVSS 0.0


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
    category: str = "exploitable"  # Default to exploitable for active modules

    def get_category(self) -> FindingCategory:
        """Determine finding category based on type and confidence."""
        # Informational findings
        info_types = [
            "Information Disclosure",
            "Server Header",
            "Cookie without Secure",
            "Cookie without HttpOnly",
        ]
        if any(t in self.vuln_type for t in info_types) or self.cvss_score == 0:
            return FindingCategory.INFORMATIONAL

        # Misconfiguration findings (header-related)
        misconfig_types = [
            "Missing Security Header",
            "X-Frame-Options",
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "CORS",
            "CSRF",
        ]
        if any(t in self.vuln_type for t in misconfig_types):
            if self.confidence == "confirmed":
                return FindingCategory.MISCONFIGURATION
            return FindingCategory.INFORMATIONAL

        # Exploitable findings (active exploitation confirmed)
        exploitable_types = [
            "SQL Injection",
            "XSS",
            "Command Injection",
            "Path Traversal",
            "SSRF",
            "XXE",
            "SSTI",
            "Open Redirect",
            "IDOR",
        ]
        if any(t in self.vuln_type for t in exploitable_types):
            if self.confidence in ["confirmed", "firm"]:
                return FindingCategory.EXPLOITABLE
            return FindingCategory.MISCONFIGURATION

        # Default based on confidence
        if self.confidence == "confirmed":
            return FindingCategory.EXPLOITABLE
        elif self.confidence == "firm":
            return FindingCategory.MISCONFIGURATION
        else:
            return FindingCategory.INFORMATIONAL


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
