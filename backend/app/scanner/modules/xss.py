import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Unique canary strings to detect reflection
XSS_CANARY = "scntm7x5s"

XSS_PAYLOADS = [
    f'<script>{XSS_CANARY}</script>',
    f'"><img src=x onerror={XSS_CANARY}>',
    f"'><svg/onload={XSS_CANARY}>",
    f'javascript:{XSS_CANARY}',
    f'" onfocus="{XSS_CANARY}" autofocus="',
]

QUICK_PAYLOADS = XSS_PAYLOADS[:2]


@ModuleRegistry.register
class XssModule(BaseModule):
    name = "xss"
    description = "Tests for reflected Cross-Site Scripting (XSS)"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        # Test query parameters for reflection
        for param_name, param_values in query_params.items():
            payloads = QUICK_PAYLOADS  # Use limited set for quick scan
            for payload in payloads:
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

                body = response.text
                if XSS_CANARY in body and payload in body:
                    # Check if payload is reflected unencoded
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="Reflected XSS",
                        severity="high",
                        cvss_score=6.1,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                        owasp_category="A03",
                        cwe_id="CWE-79",
                        affected_url=page.url,
                        affected_parameter=param_name,
                        description=f"Parameter '{param_name}' reflects user input without encoding, enabling XSS.",
                        remediation="Encode all user input before rendering in HTML context. Implement Content-Security-Policy.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "XSS Payload", "content": payload},
                            {"type": "request", "title": "Test URL", "content": test_url},
                            {"type": "response", "title": "Reflected Content (excerpt)",
                             "content": self._extract_context(body, XSS_CANARY)},
                        ],
                    ))
                    break  # One finding per parameter

        # Test form inputs
        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name"):
                    continue
                payload = XSS_PAYLOADS[0]
                data = {i["name"]: i.get("value", "test") for i in form.inputs if i.get("name")}
                data[inp["name"]] = payload

                try:
                    if form.method == "POST":
                        response = await http_client.post(form.action, data=data)
                    else:
                        test_url = f"{form.action}?{urlencode(data)}"
                        response = await http_client.get(test_url)
                except Exception:
                    continue

                if XSS_CANARY in response.text and payload in response.text:
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="Reflected XSS (Form)",
                        severity="high",
                        cvss_score=6.1,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                        owasp_category="A03",
                        cwe_id="CWE-79",
                        affected_url=form.action,
                        affected_parameter=inp["name"],
                        description=f"Form input '{inp['name']}' reflects user input without encoding.",
                        remediation="Encode all user input before rendering. Implement Content-Security-Policy.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "XSS Payload", "content": payload},
                            {"type": "response", "title": "Reflected Content (excerpt)",
                             "content": self._extract_context(response.text, XSS_CANARY)},
                        ],
                    ))
                    break

        return findings

    @staticmethod
    def _extract_context(body: str, marker: str, context_chars: int = 100) -> str:
        idx = body.find(marker)
        if idx == -1:
            return ""
        start = max(0, idx - context_chars)
        end = min(len(body), idx + len(marker) + context_chars)
        return f"...{body[start:end]}..."
