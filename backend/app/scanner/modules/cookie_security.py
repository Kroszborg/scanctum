from app.scanner.crawler import CrawledPage
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


@ModuleRegistry.register
class CookieSecurityModule(BaseModule):
    name = "cookie_security"
    description = "Checks for insecure cookie attributes"
    scan_modes = ["quick", "full"]
    is_active = False

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []
        set_cookies = []

        for key, value in page.headers.items():
            if key.lower() == "set-cookie":
                set_cookies.append(value)

        for cookie_str in set_cookies:
            parts = cookie_str.split(";")
            cookie_name = parts[0].split("=")[0].strip() if parts else "unknown"
            flags = cookie_str.lower()

            if "httponly" not in flags:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Cookie Missing HttpOnly Flag",
                    severity="low",
                    cvss_score=3.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-1004",
                    affected_url=page.url,
                    affected_parameter=cookie_name,
                    description=f"Cookie '{cookie_name}' is missing the HttpOnly flag, making it accessible to JavaScript.",
                    remediation="Add the HttpOnly flag to prevent client-side script access.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "Set-Cookie Header", "content": cookie_str}],
                ))

            if "secure" not in flags:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Cookie Missing Secure Flag",
                    severity="low",
                    cvss_score=3.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-614",
                    affected_url=page.url,
                    affected_parameter=cookie_name,
                    description=f"Cookie '{cookie_name}' is missing the Secure flag, allowing transmission over HTTP.",
                    remediation="Add the Secure flag so the cookie is only sent over HTTPS.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "Set-Cookie Header", "content": cookie_str}],
                ))

            if "samesite" not in flags:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Cookie Missing SameSite Attribute",
                    severity="low",
                    cvss_score=3.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-1275",
                    affected_url=page.url,
                    affected_parameter=cookie_name,
                    description=f"Cookie '{cookie_name}' is missing the SameSite attribute.",
                    remediation="Add 'SameSite=Lax' or 'SameSite=Strict' attribute.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "Set-Cookie Header", "content": cookie_str}],
                ))

        return findings
