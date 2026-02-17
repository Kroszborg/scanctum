from urllib.parse import urljoin

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

SENSITIVE_PATHS = [
    "/admin", "/administrator", "/wp-admin", "/phpmyadmin",
    "/backup", "/db", "/database", "/config", "/conf",
    "/api/", "/internal", "/private", "/secret", "/debug",
]


@ModuleRegistry.register
class RobotsTxtModule(BaseModule):
    name = "robots_txt"
    description = "Analyzes robots.txt for sensitive path disclosure"
    scan_modes = ["quick", "full"]
    is_active = True  # Fetches robots.txt

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        robots_url = urljoin(page.url, "/robots.txt")

        try:
            response = await http_client.get(robots_url)
        except Exception:
            return findings

        if response.status_code != 200:
            return findings

        body = response.text
        disallowed: list[str] = []

        for line in body.splitlines():
            line = line.strip()
            if line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed.append(path)

        sensitive = [p for p in disallowed if any(s in p.lower() for s in SENSITIVE_PATHS)]

        if sensitive:
            findings.append(Finding(
                module_name=self.name,
                vuln_type="Sensitive Path Disclosure in robots.txt",
                severity="info",
                cvss_score=0.0,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
                owasp_category="A01",
                cwe_id="CWE-200",
                affected_url=robots_url,
                affected_parameter=None,
                description=f"robots.txt discloses {len(sensitive)} potentially sensitive path(s).",
                remediation="Avoid listing sensitive paths in robots.txt. Use authentication and access control instead.",
                confidence="firm",
                evidence=[{
                    "type": "response",
                    "title": "Sensitive Disallow Entries",
                    "content": "\n".join(f"Disallow: {p}" for p in sensitive),
                }],
            ))

        return findings
