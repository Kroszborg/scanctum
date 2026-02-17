from urllib.parse import urljoin

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

SENSITIVE_PATHS = [
    ("/.env", "Environment Configuration File"),
    ("/.git/config", "Git Configuration"),
    ("/.git/HEAD", "Git HEAD Reference"),
    ("/wp-config.php", "WordPress Configuration"),
    ("/config.php", "PHP Configuration"),
    ("/web.config", "IIS Configuration"),
    ("/.htaccess", "Apache Configuration"),
    ("/package.json", "Node.js Package Manifest"),
    ("/composer.json", "PHP Composer Manifest"),
    ("/Gemfile", "Ruby Gemfile"),
    ("/.dockerenv", "Docker Environment"),
    ("/docker-compose.yml", "Docker Compose File"),
    ("/.aws/credentials", "AWS Credentials"),
    ("/phpinfo.php", "PHP Info Page"),
    ("/server-status", "Apache Server Status"),
    ("/elmah.axd", ".NET Error Log"),
    ("/.DS_Store", "macOS Directory Store"),
    ("/crossdomain.xml", "Flash Cross-Domain Policy"),
    ("/sitemap.xml", "Sitemap (Info Disclosure)"),
    ("/debug/", "Debug Endpoint"),
]

CONTENT_INDICATORS = {
    "/.env": ["DB_PASSWORD", "APP_KEY", "SECRET", "DATABASE_URL"],
    "/.git/config": ["[core]", "[remote", "repositoryformatversion"],
    "/.git/HEAD": ["ref: refs/heads/"],
    "/phpinfo.php": ["phpinfo()", "PHP Version"],
    "/server-status": ["Apache Server Status", "Total accesses"],
}


@ModuleRegistry.register
class SensitiveFilesModule(BaseModule):
    name = "sensitive_files"
    description = "Checks for exposed sensitive files and configuration"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        base = page.url

        for path, desc in SENSITIVE_PATHS:
            test_url = urljoin(base, path)
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            if response.status_code != 200:
                continue

            # Verify with content indicators if available
            indicators = CONTENT_INDICATORS.get(path)
            if indicators:
                if not any(ind in response.text for ind in indicators):
                    continue

            severity = "high" if path in ("/.env", "/.git/config", "/.aws/credentials", "/wp-config.php") else "medium"
            score = 7.5 if severity == "high" else 5.3

            findings.append(Finding(
                module_name=self.name,
                vuln_type=f"Exposed Sensitive File: {desc}",
                severity=severity,
                cvss_score=score,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N" if severity == "high"
                else "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                owasp_category="A05",
                cwe_id="CWE-538",
                affected_url=test_url,
                affected_parameter=None,
                description=f"Sensitive file '{path}' is publicly accessible.",
                remediation=f"Block access to '{path}' in web server configuration. Remove sensitive files from the web root.",
                confidence="confirmed",
                evidence=[{
                    "type": "response",
                    "title": "Response Preview",
                    "content": response.text[:500],
                }],
            ))

        return findings
