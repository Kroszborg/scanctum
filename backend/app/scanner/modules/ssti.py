"""Server-Side Template Injection (SSTI) scanner module."""
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# SSTI probes: expression → expected output (math evaluation)
# If the expression is evaluated server-side, the output will be the result.
SSTI_PROBES = [
    # Jinja2/Twig/Twirl: {{7*7}} → 49
    ("{{7*7}}", "49"),
    # Jinja2 string mul: {{'7'*7}} → 7777777
    ("{{'7'*7}}", "7777777"),
    # Freemarker / Velocity: ${7*7} → 49
    ("${7*7}", "49"),
    # Smarty: {7*7} → 49
    ("{7*7}", "49"),
    # ERB: <%= 7*7 %> → 49
    ("<%= 7*7 %>", "49"),
    # Mako: ${7*7} → 49 (same as Freemarker)
    # Tornado: {{ 7*7 }} → 49
    ("{{ 7*7 }}", "49"),
    # Pebble: {{ 7*7 }}
    ("{{7*'7'}}", "7777777"),
]

SSTI_PATTERN = re.compile(r"\b49\b|\b7777777\b")


@ModuleRegistry.register
class SstiModule(BaseModule):
    name = "ssti"
    description = "Tests for Server-Side Template Injection (SSTI)"
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

        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name"):
                    continue
                finding = await self._test_form(page, form, inp, http_client)
                if finding:
                    findings.append(finding)
                    break

        return findings

    async def _test_param(self, page, param_name, query_params, parsed, http_client) -> Finding | None:
        # First, get baseline response to check if expression appears in output
        baseline_params = {k: v[0] for k, v in query_params.items()}
        try:
            baseline_resp = await http_client.get(page.url)
        except Exception:
            return None

        for probe, expected in SSTI_PROBES:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = probe
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            # Check if the math was evaluated (result appears but raw probe doesn't)
            if (expected in response.text
                    and probe not in response.text
                    and expected not in baseline_resp.text):
                return Finding(
                    module_name=self.name,
                    vuln_type="Server-Side Template Injection (SSTI)",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-94",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Parameter '{param_name}' is vulnerable to SSTI. "
                        f"Template expression '{probe}' was evaluated to '{expected}'."
                    ),
                    remediation=(
                        "Never pass user input directly into template engines. "
                        "Use sandboxed template environments. Validate and sanitize all user inputs."
                    ),
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "SSTI Probe", "content": f"{probe} → expected '{expected}'"},
                        {"type": "request", "title": "Test URL", "content": test_url},
                        {"type": "response", "title": "Evaluated Output", "content": self._extract_context(response.text, expected)},
                    ],
                )
        return None

    async def _test_form(self, page, form, inp, http_client) -> Finding | None:
        for probe, expected in SSTI_PROBES[:3]:
            data = {i["name"]: i.get("value", "test") for i in form.inputs if i.get("name")}
            data[inp["name"]] = probe
            try:
                if form.method == "POST":
                    response = await http_client.post(form.action, data=data)
                else:
                    test_url = f"{form.action}?{urlencode(data)}"
                    response = await http_client.get(test_url)
            except Exception:
                continue

            if expected in response.text and probe not in response.text:
                return Finding(
                    module_name=self.name,
                    vuln_type="Server-Side Template Injection (SSTI) - Form",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-94",
                    affected_url=form.action,
                    affected_parameter=inp["name"],
                    description=f"Form input '{inp['name']}' is vulnerable to SSTI. Expression evaluated server-side.",
                    remediation="Never pass user input into template engines unsanitized. Use strict sandboxing.",
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "SSTI Probe", "content": f"{probe} → '{expected}'"},
                        {"type": "response", "title": "Evaluated Output", "content": self._extract_context(response.text, expected)},
                    ],
                )
        return None

    @staticmethod
    def _extract_context(text: str, marker: str, context: int = 80) -> str:
        idx = text.find(marker)
        if idx == -1:
            return ""
        start = max(0, idx - context)
        end = min(len(text), idx + len(marker) + context)
        return f"...{text[start:end]}..."
