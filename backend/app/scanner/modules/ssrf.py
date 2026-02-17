from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

URL_PARAMS = ["url", "uri", "path", "src", "href", "link", "redirect", "fetch", "proxy", "load", "page", "file"]

SSRF_PAYLOADS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://[::1]",
    "http://0177.0.0.1",
    "http://2130706433",
]

SSRF_INDICATORS = [
    "root:", "/bin/", "localhost", "127.0.0.1",
    "Windows", "Apache", "nginx",
    "Connection refused", "No route to host",
]


@ModuleRegistry.register
class SsrfModule(BaseModule):
    name = "ssrf"
    description = "Tests for Server-Side Request Forgery"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        for param_name in query_params:
            if param_name.lower() not in URL_PARAMS:
                continue

            for payload in SSRF_PAYLOADS:
                test_params = {k: v[0] for k, v in query_params.items()}
                test_params[param_name] = payload
                test_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    "", urlencode(test_params), "",
                ))

                try:
                    response = await http_client.get(test_url)
                except Exception:
                    continue

                for indicator in SSRF_INDICATORS:
                    if indicator in response.text:
                        findings.append(Finding(
                            module_name=self.name,
                            vuln_type="Server-Side Request Forgery (SSRF)",
                            severity="high",
                            cvss_score=7.5,
                            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            owasp_category="A10",
                            cwe_id="CWE-918",
                            affected_url=page.url,
                            affected_parameter=param_name,
                            description=f"Parameter '{param_name}' may be vulnerable to SSRF. Internal content indicator found.",
                            remediation="Validate and sanitize URL parameters. Use allowlists for permitted domains. Block internal/private IP ranges.",
                            confidence="tentative",
                            evidence=[
                                {"type": "payload", "title": "SSRF Payload", "content": payload},
                                {"type": "response", "title": "Response Indicator", "content": indicator},
                            ],
                        ))
                        return findings

        return findings
