"""Command injection scanner module."""
import re
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# A unique canary that won't appear in normal responses
CANARY = "scntm_cmd_7x9z"

# Payloads that print the canary if executed
OUTPUT_PAYLOADS = [
    f"; echo {CANARY}",
    f"| echo {CANARY}",
    f"& echo {CANARY}",
    f"`echo {CANARY}`",
    f"$(echo {CANARY})",
    f"; echo {CANARY} #",
    f"|| echo {CANARY}",
    f"&& echo {CANARY}",
    # Windows equivalents
    f"& echo {CANARY} &",
    f"| type C:\\windows\\win.ini",  # Windows indicator
]

# Time-based payloads (blind) — 5s sleep
TIME_PAYLOADS = [
    ("; sleep 5", 5),
    ("| sleep 5", 5),
    ("`sleep 5`", 5),
    ("$(sleep 5)", 5),
    ("& ping -n 6 127.0.0.1", 5),   # Windows: 6 pings ≈ 5s
    ("; sleep 5 #", 5),
]

WINDOWS_INDICATOR = re.compile(r"\[extensions\]|for 16-bit app support", re.I)


@ModuleRegistry.register
class CommandInjectionModule(BaseModule):
    name = "command_injection"
    description = "Tests for OS command injection vulnerabilities"
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
        # Output-based detection
        for payload in OUTPUT_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = f"test{payload}"
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            if CANARY in response.text:
                return Finding(
                    module_name=self.name,
                    vuln_type="OS Command Injection",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-78",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Parameter '{param_name}' is vulnerable to OS command injection. "
                        f"Command output canary '{CANARY}' appeared in the response."
                    ),
                    remediation=(
                        "Never pass user input to shell commands. Use language APIs instead of shell calls. "
                        "If shell is required, use allowlist validation and shell escaping."
                    ),
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "Command Injection Payload", "content": payload},
                        {"type": "request", "title": "Test URL", "content": test_url},
                        {"type": "response", "title": "Command Output", "content": self._extract_context(response.text, CANARY)},
                    ],
                )

            if WINDOWS_INDICATOR.search(response.text):
                return Finding(
                    module_name=self.name,
                    vuln_type="OS Command Injection (Windows)",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-78",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=f"Parameter '{param_name}' is vulnerable to Windows command injection. win.ini content was disclosed.",
                    remediation="Never pass user input to shell commands. Use allowlists and proper escaping.",
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "Payload", "content": payload},
                        {"type": "response", "title": "win.ini Content Found", "content": "Windows file content detected in response"},
                    ],
                )

        # Time-based (blind) detection
        for payload, expected_delay in TIME_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = f"test{payload}"
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                start = time.monotonic()
                await http_client.get(test_url)
                elapsed = time.monotonic() - start
            except Exception:
                continue

            if elapsed >= expected_delay - 1:
                return Finding(
                    module_name=self.name,
                    vuln_type="OS Command Injection - Blind (Time-Based)",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-78",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Blind command injection detected in '{param_name}'. "
                        f"Response delayed by ~{elapsed:.1f}s after sleep command."
                    ),
                    remediation="Never pass user input to OS commands. Validate and sanitize all inputs rigorously.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "Time Payload", "content": payload},
                        {"type": "log", "title": "Response Delay", "content": f"{elapsed:.2f}s (expected {expected_delay}s)"},
                    ],
                )

        return None

    async def _test_form(self, page, form, inp, http_client) -> Finding | None:
        for payload in OUTPUT_PAYLOADS[:4]:
            data = {i["name"]: i.get("value", "test") for i in form.inputs if i.get("name")}
            data[inp["name"]] = f"test{payload}"
            try:
                if form.method == "POST":
                    response = await http_client.post(form.action, data=data)
                else:
                    test_url = f"{form.action}?{urlencode(data)}"
                    response = await http_client.get(test_url)
            except Exception:
                continue

            if CANARY in response.text:
                return Finding(
                    module_name=self.name,
                    vuln_type="OS Command Injection (Form)",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-78",
                    affected_url=form.action,
                    affected_parameter=inp["name"],
                    description=f"Form field '{inp['name']}' is vulnerable to OS command injection.",
                    remediation="Never pass form input to shell commands. Use parameterized APIs.",
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "Payload", "content": payload},
                        {"type": "response", "title": "Command Output", "content": self._extract_context(response.text, CANARY)},
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
