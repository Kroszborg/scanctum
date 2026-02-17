import re
from urllib.parse import urlparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Patterns that suggest sequential/guessable IDs in URLs
ID_PATTERNS = [
    re.compile(r"/(\d{1,8})(?:/|$|\?)"),  # Numeric IDs in path
    re.compile(r"[?&]id=(\d+)"),
    re.compile(r"[?&]user_id=(\d+)"),
    re.compile(r"[?&]account=(\d+)"),
    re.compile(r"[?&]order=(\d+)"),
]


@ModuleRegistry.register
class IdorModule(BaseModule):
    name = "idor"
    description = "Tests for Insecure Direct Object References"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        url = page.url

        for pattern in ID_PATTERNS:
            match = pattern.search(url)
            if not match:
                continue

            original_id = match.group(1)
            try:
                test_id = str(int(original_id) + 1)
            except ValueError:
                continue

            test_url = url[:match.start(1)] + test_id + url[match.end(1):]

            try:
                original_resp = await http_client.get(url)
                test_resp = await http_client.get(test_url)
            except Exception:
                continue

            # If incrementing ID returns 200 with different content, possible IDOR
            if (test_resp.status_code == 200
                    and original_resp.status_code == 200
                    and len(test_resp.text) > 100
                    and test_resp.text != original_resp.text):
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Potential IDOR",
                    severity="high",
                    cvss_score=6.5,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
                    owasp_category="A01",
                    cwe_id="CWE-639",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=f"Incrementing numeric ID ({original_id} → {test_id}) returns different content, suggesting IDOR.",
                    remediation="Implement authorization checks on every object access. Use unpredictable identifiers (UUIDs).",
                    confidence="tentative",
                    evidence=[
                        {"type": "request", "title": "Original URL", "content": url},
                        {"type": "request", "title": "Manipulated URL", "content": test_url},
                        {"type": "log", "title": "Response Sizes",
                         "content": f"Original: {len(original_resp.text)} bytes\nModified: {len(test_resp.text)} bytes"},
                    ],
                ))
                break

        return findings
