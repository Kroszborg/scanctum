from app.scanner.crawler import CrawledPage
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

RECOMMENDED_HEADERS = {
    "Strict-Transport-Security": {
        "severity": "medium",
        "cvss_score": 5.4,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
        "cwe_id": "CWE-523",
        "remediation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' header.",
    },
    "X-Content-Type-Options": {
        "severity": "low",
        "cvss_score": 3.1,
        "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        "cwe_id": "CWE-16",
        "remediation": "Add 'X-Content-Type-Options: nosniff' header.",
    },
    "X-Frame-Options": {
        "severity": "medium",
        "cvss_score": 4.3,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
        "cwe_id": "CWE-1021",
        "remediation": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' header.",
    },
    "Content-Security-Policy": {
        "severity": "medium",
        "cvss_score": 5.4,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
        "cwe_id": "CWE-16",
        "remediation": "Implement a Content-Security-Policy header with appropriate directives.",
    },
    "X-XSS-Protection": {
        "severity": "low",
        "cvss_score": 3.1,
        "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        "cwe_id": "CWE-16",
        "remediation": "Add 'X-XSS-Protection: 1; mode=block' header (or rely on CSP).",
    },
    "Referrer-Policy": {
        "severity": "low",
        "cvss_score": 3.1,
        "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        "cwe_id": "CWE-116",
        "remediation": "Add 'Referrer-Policy: strict-origin-when-cross-origin' header.",
    },
    "Permissions-Policy": {
        "severity": "low",
        "cvss_score": 3.1,
        "cvss_vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        "cwe_id": "CWE-16",
        "remediation": "Add Permissions-Policy header to control browser features.",
    },
}

INFO_DISCLOSURE_HEADERS = ["Server", "X-Powered-By", "X-AspNet-Version"]


@ModuleRegistry.register
class SecurityHeadersModule(BaseModule):
    name = "security_headers"
    description = "Checks for missing or misconfigured security headers"
    scan_modes = ["quick", "full"]
    is_active = False

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []
        headers_lower = {k.lower(): v for k, v in page.headers.items()}

        # Check missing recommended headers
        for header_name, info in RECOMMENDED_HEADERS.items():
            if header_name.lower() not in headers_lower:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type=f"Missing Security Header: {header_name}",
                    severity=info["severity"],
                    cvss_score=info["cvss_score"],
                    cvss_vector=info["cvss_vector"],
                    owasp_category="A05",
                    cwe_id=info["cwe_id"],
                    affected_url=page.url,
                    affected_parameter=None,
                    description=f"The HTTP response is missing the '{header_name}' security header.",
                    remediation=info["remediation"],
                    confidence="confirmed",
                    evidence=[{
                        "type": "response",
                        "title": "Response Headers",
                        "content": "\n".join(f"{k}: {v}" for k, v in page.headers.items()),
                    }],
                ))

        # Check info disclosure headers
        for header_name in INFO_DISCLOSURE_HEADERS:
            if header_name.lower() in headers_lower:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type=f"Information Disclosure: {header_name} Header",
                    severity="info",
                    cvss_score=0.0,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-200",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=f"The '{header_name}' header discloses server information: {headers_lower[header_name.lower()]}",
                    remediation=f"Remove or suppress the '{header_name}' header in production.",
                    confidence="confirmed",
                    evidence=[{
                        "type": "response",
                        "title": f"{header_name} Value",
                        "content": f"{header_name}: {headers_lower[header_name.lower()]}",
                    }],
                ))

        return findings
