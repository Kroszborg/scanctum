from urllib.parse import urlparse

from app.scanner.crawler import CrawledPage
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


@ModuleRegistry.register
class HttpsCheckModule(BaseModule):
    name = "https_check"
    description = "Checks for HTTPS usage and mixed content"
    scan_modes = ["quick", "full"]
    is_active = False

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)

        if parsed.scheme == "http":
            findings.append(Finding(
                module_name=self.name,
                vuln_type="Missing HTTPS",
                severity="medium",
                cvss_score=5.9,
                cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N",
                owasp_category="A02",
                cwe_id="CWE-319",
                affected_url=page.url,
                affected_parameter=None,
                description="The page is served over plain HTTP, allowing potential eavesdropping and MITM attacks.",
                remediation="Enforce HTTPS across the entire application. Redirect all HTTP traffic to HTTPS and enable HSTS.",
                confidence="confirmed",
            ))

        # Check for mixed content
        if parsed.scheme == "https":
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.body, "lxml")
            mixed = []
            for tag in soup.find_all(["script", "link", "img", "iframe"], src=True):
                src = tag.get("src", "")
                if src.startswith("http://"):
                    mixed.append(src)
            for tag in soup.find_all("link", href=True):
                href = tag.get("href", "")
                if href.startswith("http://"):
                    mixed.append(href)

            if mixed:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Mixed Content",
                    severity="low",
                    cvss_score=3.7,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A02",
                    cwe_id="CWE-311",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=f"The HTTPS page loads {len(mixed)} resource(s) over plain HTTP.",
                    remediation="Update all resource references to use HTTPS.",
                    confidence="confirmed",
                    evidence=[{
                        "type": "log",
                        "title": "Mixed Content Resources",
                        "content": "\n".join(mixed[:10]),
                    }],
                ))

        return findings
