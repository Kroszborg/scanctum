from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

REDIRECT_PARAMS = ["url", "redirect", "next", "return", "returnTo", "goto", "target", "redir", "destination", "continue"]
REDIRECT_PAYLOADS = [
    "https://evil.com",
    "//evil.com",
    "/\\evil.com",
]


@ModuleRegistry.register
class OpenRedirectModule(BaseModule):
    name = "open_redirect"
    description = "Tests for open redirect vulnerabilities"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        # Test URL query parameters
        for param_name in query_params:
            if param_name.lower() not in [p.lower() for p in REDIRECT_PARAMS]:
                continue

            for payload in REDIRECT_PAYLOADS:
                test_params = {**{k: v[0] for k, v in query_params.items()}}
                test_params[param_name] = payload
                test_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    "", urlencode(test_params), "",
                ))

                try:
                    response = await http_client.client.request(
                        "GET", test_url, follow_redirects=False,
                    )
                except Exception:
                    continue

                location = response.headers.get("location", "")
                if response.status_code in (301, 302, 303, 307, 308):
                    loc_host = urlparse(location).hostname or ""
                    if "evil.com" in loc_host:
                        findings.append(Finding(
                            module_name=self.name,
                            vuln_type="Open Redirect",
                            severity="medium",
                            cvss_score=6.1,
                            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                            owasp_category="A01",
                            cwe_id="CWE-601",
                            affected_url=page.url,
                            affected_parameter=param_name,
                            description=f"Parameter '{param_name}' allows redirects to external domains.",
                            remediation="Validate redirect targets against a whitelist of allowed domains. Use relative paths when possible.",
                            confidence="confirmed",
                            evidence=[
                                {"type": "request", "title": "Test URL", "content": test_url},
                                {"type": "response", "title": "Redirect Location", "content": f"Location: {location}"},
                            ],
                        ))
                        return findings  # One finding per page is sufficient

        return findings
