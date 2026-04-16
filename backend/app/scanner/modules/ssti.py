"""Server-Side Template Injection (SSTI) scanner module with improved validation."""
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry
from app.scanner.modules.validation import (
    ConfidenceFactors,
    create_validated_finding,
    detect_waf,
)

# SSTI probes: expression → expected output (math evaluation)
# Using unique numbers to avoid false positives
SSTI_PROBES = [
    # Jinja2/Twig/Twirl: {{7*7}} → 49
    ("{{{{7*7}}}}", "49"),
    # Jinja2 string mul: {{'7'*7}} → 7777777 (unique pattern)
    ("{{{{'7'*7}}}}", "7777777"),
    # Freemarker / Velocity: ${7*7} → 49
    ("${{{7*7}}}", "49"),
    # ERB: <%= 7*7 %> → 49
    ("<%= 7*7 %>", "49"),
    # Tornado: {{ 7*7 }} → 49
    ("{{ 7*7 }}", "49"),
    # Additional probe with unique number
    ("{{{{5555*5555}}}}", "30858025"),  # Very unique result
]

# Patterns that indicate template processing (not just numbers)
SSTI_INDICATORS = [
    re.compile(r"error.*template", re.I),
    re.compile(r"template.*exception", re.I),
    re.compile(r"jinja2", re.I),
    re.compile(r"freemarker", re.I),
    re.compile(r"velocity", re.I),
    re.compile(r"twig", re.I),
]


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
        confirmed_probes = 0
        last_finding = None

        # First, get baseline response to check if expected values appear naturally
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

            # Strict check: expected result appears, probe doesn't, and expected not in baseline
            if (expected in response.text
                    and probe not in response.text
                    and expected not in baseline_resp.text):

                # Check for template error indicators
                has_template_error = any(
                    pattern.search(response.text) for pattern in SSTI_INDICATORS
                )

                confirmed_probes += 1

                # Check for WAF
                waf_detected = detect_waf(response.text)

                factors = ConfidenceFactors(
                    error_pattern_match=has_template_error,
                    multiple_payloads_success=confirmed_probes >= 2,
                    waf_detected=waf_detected,
                )

                last_finding = create_validated_finding(
                    module_name=self.name,
                    vuln_type="Server-Side Template Injection (SSTI)",
                    base_severity="critical" if confirmed_probes >= 2 else "high",
                    base_cvss=9.8 if confirmed_probes >= 2 else 7.5,
                    base_cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
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
                    confidence_factors=factors,
                    evidence=[
                        {"type": "payload", "title": "SSTI Probe", "content": f"{probe} → expected '{expected}'"},
                        {"type": "request", "title": "Test URL", "content": test_url},
                        {"type": "response", "title": "Evaluated Output", "content": self._extract_context(response.text, expected)},
                    ],
                )

                # If we have 2+ confirmed probes and template error, return immediately
                if confirmed_probes >= 2 and has_template_error:
                    break

        # Require at least 2 confirmed probes to report (reduces false positives)
        if confirmed_probes >= 2:
            return last_finding
        return None

    async def _test_form(self, page, form, inp, http_client) -> Finding | None:
        confirmed_probes = 0
        last_finding = None

        for probe, expected in SSTI_PROBES[:4]:
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

            # Strict check: expected result must appear, probe must NOT appear
            # Also check it's not in baseline (page content)
            if (expected in response.text
                    and probe not in response.text
                    and expected not in page.response_text):  # Not in baseline

                # Check for template error indicators
                has_template_error = any(
                    pattern.search(response.text) for pattern in SSTI_INDICATORS
                )

                confirmed_probes += 1

                # Check for WAF
                waf_detected = detect_waf(response.text)

                last_finding = Finding(
                    module_name=self.name,
                    vuln_type="Server-Side Template Injection (SSTI) - Form",
                    severity="critical" if confirmed_probes >= 2 else "high",
                    cvss_score=9.8 if confirmed_probes >= 2 else 7.5,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-94",
                    affected_url=form.action,
                    affected_parameter=inp["name"],
                    description=f"Form input '{inp['name']}' is vulnerable to SSTI. Expression evaluated server-side.",
                    remediation="Never pass user input into template engines unsanitized. Use strict sandboxing.",
                    confidence="confirmed" if confirmed_probes >= 2 else "tentative",
                    evidence=[
                        {"type": "payload", "title": "SSTI Probe", "content": f"{probe} → '{expected}'"},
                        {"type": "response", "title": "Evaluated Output", "content": self._extract_context(response.text, expected)},
                    ],
                )

                # If we have 2+ confirmed probes and template error, return immediately
                if confirmed_probes >= 2 and has_template_error:
                    break

        # Require at least 2 confirmed probes to report (reduces false positives)
        if confirmed_probes >= 2:
            return last_finding
        return None

    @staticmethod
    def _extract_context(text: str, marker: str, context: int = 80) -> str:
        idx = text.find(marker)
        if idx == -1:
            return ""
        start = max(0, idx - context)
        end = min(len(text), idx + len(marker) + context)
        return f"...{text[start:end]}..."
