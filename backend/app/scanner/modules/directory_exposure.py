from urllib.parse import urljoin

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

DIRECTORY_INDICATORS = [
    "Index of /",
    "Directory listing for",
    "<title>Directory listing",
    "Parent Directory</a>",
]

COMMON_DIRS = [
    "/backup/", "/backups/", "/tmp/", "/temp/",
    "/uploads/", "/logs/", "/log/",
    "/.git/", "/.svn/", "/.env",
    "/config/", "/conf/", "/debug/",
]


@ModuleRegistry.register
class DirectoryExposureModule(BaseModule):
    name = "directory_exposure"
    description = "Checks for directory listing and exposed directories"
    scan_modes = ["quick", "full"]
    is_active = True

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []
        for indicator in DIRECTORY_INDICATORS:
            if indicator.lower() in page.body.lower():
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Directory Listing Enabled",
                    severity="medium",
                    cvss_score=5.3,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-548",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="Directory listing is enabled, exposing file structure to attackers.",
                    remediation="Disable directory listing in web server configuration.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "Directory Listing Indicator",
                               "content": indicator}],
                ))
                break
        return findings

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        base = page.url

        for dir_path in COMMON_DIRS:
            test_url = urljoin(base, dir_path)
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            if response.status_code == 200:
                body = response.text.lower()
                if any(ind.lower() in body for ind in DIRECTORY_INDICATORS):
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="Exposed Directory",
                        severity="medium",
                        cvss_score=5.3,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                        owasp_category="A05",
                        cwe_id="CWE-548",
                        affected_url=test_url,
                        affected_parameter=None,
                        description=f"Directory listing accessible at {dir_path}.",
                        remediation="Disable directory listing and restrict access to sensitive directories.",
                        confidence="confirmed",
                        evidence=[{"type": "request", "title": "Test URL", "content": test_url}],
                    ))

        return findings
