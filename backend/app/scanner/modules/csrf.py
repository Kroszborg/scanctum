from app.scanner.crawler import CrawledPage
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

CSRF_TOKEN_NAMES = {
    "csrf_token", "csrfmiddlewaretoken", "_token", "authenticity_token",
    "csrf", "__requestverificationtoken", "antiforgery", "_csrf",
}


@ModuleRegistry.register
class CsrfModule(BaseModule):
    name = "csrf"
    description = "Checks for missing CSRF protection on forms"
    scan_modes = ["full"]
    is_active = False

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []

        for form in page.forms:
            if form.method != "POST":
                continue

            input_names = {inp.get("name", "").lower() for inp in form.inputs}
            has_csrf = bool(input_names & CSRF_TOKEN_NAMES)

            if not has_csrf:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Missing CSRF Protection",
                    severity="medium",
                    cvss_score=4.3,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
                    owasp_category="A01",
                    cwe_id="CWE-352",
                    affected_url=form.action,
                    affected_parameter=None,
                    description=f"POST form at '{form.action}' has no CSRF token.",
                    remediation="Add a CSRF token to all state-changing forms. Use SameSite cookie attribute as defense-in-depth.",
                    confidence="firm",
                    evidence=[{
                        "type": "log",
                        "title": "Form Details",
                        "content": f"Method: {form.method}\nAction: {form.action}\nInputs: {', '.join(input_names)}",
                    }],
                ))

        return findings
