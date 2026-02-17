from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


@ModuleRegistry.register
class CorsModule(BaseModule):
    name = "cors"
    description = "Tests for CORS misconfiguration"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        test_origins = [
            "https://evil.com",
            "null",
        ]

        for origin in test_origins:
            try:
                response = await http_client.client.request(
                    "GET",
                    page.url,
                    headers={"Origin": origin},
                )
            except Exception:
                continue

            acao = response.headers.get("access-control-allow-origin", "")
            acac = response.headers.get("access-control-allow-credentials", "").lower()

            if acao == "*" and acac == "true":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Wildcard with Credentials",
                    severity="high",
                    cvss_score=8.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="CORS allows any origin with credentials, enabling cross-origin data theft.",
                    remediation="Never combine Access-Control-Allow-Origin: * with credentials. Whitelist specific origins.",
                    confidence="confirmed",
                    evidence=[{
                        "type": "response",
                        "title": "CORS Headers",
                        "content": f"Access-Control-Allow-Origin: {acao}\nAccess-Control-Allow-Credentials: {acac}",
                    }],
                ))
                break

            if origin != "null" and acao == origin:
                severity = "high" if acac == "true" else "medium"
                score = 8.1 if acac == "true" else 5.4
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Origin Reflection",
                    severity=severity,
                    cvss_score=score,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N" if severity == "high"
                    else "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=f"CORS reflects arbitrary origin '{origin}' in Access-Control-Allow-Origin.",
                    remediation="Validate origins against a whitelist instead of reflecting the request origin.",
                    confidence="confirmed",
                    evidence=[{
                        "type": "request",
                        "title": "Test Request",
                        "content": f"Origin: {origin}",
                    }, {
                        "type": "response",
                        "title": "CORS Headers",
                        "content": f"Access-Control-Allow-Origin: {acao}\nAccess-Control-Allow-Credentials: {acac}",
                    }],
                ))
                break

            if acao == "null":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Null Origin Allowed",
                    severity="medium",
                    cvss_score=5.4,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="CORS allows the 'null' origin, which can be exploited via sandboxed iframes.",
                    remediation="Do not allow 'null' as a valid origin in CORS configuration.",
                    confidence="confirmed",
                    evidence=[{
                        "type": "response",
                        "title": "CORS Headers",
                        "content": f"Access-Control-Allow-Origin: {acao}",
                    }],
                ))
                break

        return findings
