"""CRLF Injection scanner module."""
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Canary header we inject — if it appears in response headers, CRLF is confirmed
CRLF_HEADER_NAME = "X-Scntm-Crlf"
CRLF_HEADER_VALUE = "injected"

# CRLF payloads: various encodings of \r\n
CRLF_PAYLOADS = [
    f"\r\n{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    f"%0d%0a{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    f"%0D%0A{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    f"%0d%0a%20{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    f"\r\n\t{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    f"%E5%98%8D%E5%98%8A{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",  # Unicode CRLF
    f"\\r\\n{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}",
    # Log injection payloads (appear in body)
    "\r\n\r\n<html>injected</html>",
    "%0d%0a%0d%0a<html>injected</html>",
]

BODY_INJECTION_PATTERN = re.compile(r"<html>injected</html>", re.I)


@ModuleRegistry.register
class CrlfInjectionModule(BaseModule):
    name = "crlf_injection"
    description = "Tests for CRLF (HTTP response splitting / header injection) vulnerabilities"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        for param_name in query_params:
            finding = await self._test_param(page, param_name, query_params, parsed, http_client)
            if finding:
                findings.append(finding)

        return findings

    async def _test_param(self, page, param_name, query_params, parsed, http_client) -> Finding | None:
        for payload in CRLF_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = f"test{payload}"
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            # Check for header injection
            if CRLF_HEADER_NAME.lower() in response.headers:
                return Finding(
                    module_name=self.name,
                    vuln_type="CRLF Injection / HTTP Header Injection",
                    severity="high",
                    cvss_score=6.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                    owasp_category="A03",
                    cwe_id="CWE-113",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Parameter '{param_name}' is vulnerable to CRLF injection. "
                        f"The injected header '{CRLF_HEADER_NAME}: {CRLF_HEADER_VALUE}' "
                        "appeared in the HTTP response headers, enabling response splitting."
                    ),
                    remediation=(
                        "Strip or encode CR (\\r) and LF (\\n) characters before including "
                        "user input in HTTP response headers. Use framework-provided header APIs."
                    ),
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "CRLF Payload", "content": repr(payload)},
                        {"type": "request", "title": "Test URL", "content": test_url},
                        {"type": "response", "title": "Injected Header", "content": f"{CRLF_HEADER_NAME}: {response.headers.get(CRLF_HEADER_NAME.lower(), '')}"},
                    ],
                )

            # Check for response body injection (HTTP splitting leads to body)
            if BODY_INJECTION_PATTERN.search(response.text):
                return Finding(
                    module_name=self.name,
                    vuln_type="HTTP Response Splitting",
                    severity="high",
                    cvss_score=6.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                    owasp_category="A03",
                    cwe_id="CWE-113",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Parameter '{param_name}' is vulnerable to HTTP response splitting. "
                        "Injected content appeared in response body via CRLF sequences."
                    ),
                    remediation="Sanitize CRLF sequences in all user-supplied data reflected in HTTP responses.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "CRLF Payload", "content": repr(payload)},
                        {"type": "response", "title": "Injected Content Found", "content": "Injected HTML found in response body"},
                    ],
                )

        return None
