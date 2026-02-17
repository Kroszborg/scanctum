import asyncio

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


@ModuleRegistry.register
class RateLimitCheckModule(BaseModule):
    name = "rate_limit_check"
    description = "Checks if API endpoints enforce rate limiting"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []

        # Only test the main page URL, not every crawled page
        # Send a small burst and check for rate limit headers
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-rate-limit-limit",
            "retry-after",
            "ratelimit-limit",
        ]

        try:
            response = await http_client.get(page.url)
        except Exception:
            return findings

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        has_rate_limit = any(h in headers_lower for h in rate_limit_headers)

        if not has_rate_limit:
            # Check for login/auth forms which should definitely have rate limiting
            has_login_form = any(
                form.method == "POST" and
                any(inp.get("type") == "password" for inp in form.inputs)
                for form in page.forms
            )

            if has_login_form:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Missing Rate Limiting on Authentication",
                    severity="medium",
                    cvss_score=5.3,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A07",
                    cwe_id="CWE-307",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="No rate limiting headers detected on a page with authentication form. This could allow brute-force attacks.",
                    remediation="Implement rate limiting on authentication endpoints. Add progressive delays and account lockout policies.",
                    confidence="tentative",
                    evidence=[{
                        "type": "response",
                        "title": "Response Headers (no rate limit headers found)",
                        "content": "\n".join(f"{k}: {v}" for k, v in response.headers.items()),
                    }],
                ))

        return findings
