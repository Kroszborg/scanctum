import re
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Error patterns indicating SQL injection
SQL_ERRORS = [
    re.compile(r"you have an error in your sql syntax", re.I),
    re.compile(r"warning.*mysql", re.I),
    re.compile(r"unclosed quotation mark", re.I),
    re.compile(r"microsoft ole db provider for sql server", re.I),
    re.compile(r"ORA-\d{5}", re.I),
    re.compile(r"PostgreSQL.*ERROR", re.I),
    re.compile(r"sqlite3\.OperationalError", re.I),
    re.compile(r"pg_query\(\)", re.I),
    re.compile(r"SQLite/JDBCDriver", re.I),
    re.compile(r"SQL syntax.*MySQL", re.I),
    re.compile(r"valid MySQL result", re.I),
    re.compile(r"Npgsql\.PostgresException", re.I),
    re.compile(r"SQLSTATE\[", re.I),
]

ERROR_PAYLOADS = ["'", '"', "' OR '1'='1", "1' AND '1'='1", "1 AND 1=1", "' OR 1=1--"]

BOOLEAN_PAIRS = [
    ("1 AND 1=1", "1 AND 1=2"),
    ("' OR '1'='1' --", "' OR '1'='2' --"),
]

TIME_PAYLOADS = [
    ("' OR SLEEP(5)--", 5),
    ("'; WAITFOR DELAY '0:0:5'--", 5),
    ("' OR pg_sleep(5)--", 5),
]


@ModuleRegistry.register
class SqliModule(BaseModule):
    name = "sqli"
    description = "Tests for SQL Injection (error-based, boolean-blind, time-based)"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        # Test query parameters
        for param_name in query_params:
            finding = await self._test_param_url(page, param_name, query_params, parsed, http_client)
            if finding:
                findings.append(finding)

        # Test form inputs
        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name"):
                    continue
                finding = await self._test_param_form(page, form, inp, http_client)
                if finding:
                    findings.append(finding)

        return findings

    async def _test_param_url(self, page, param_name, query_params, parsed, http_client) -> Finding | None:
        # Error-based detection
        for payload in ERROR_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = payload
            test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""))

            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            for pattern in SQL_ERRORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="SQL Injection - Error Based",
                        severity="critical",
                        cvss_score=9.8,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        owasp_category="A03",
                        cwe_id="CWE-89",
                        affected_url=page.url,
                        affected_parameter=param_name,
                        description=f"SQL error detected in response when injecting into parameter '{param_name}'.",
                        remediation="Use parameterized queries or prepared statements. Never concatenate user input into SQL.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Payload", "content": payload},
                            {"type": "request", "title": "Test URL", "content": test_url},
                            {"type": "response", "title": "SQL Error", "content": pattern.pattern},
                        ],
                    )

        # Boolean-blind detection
        for true_payload, false_payload in BOOLEAN_PAIRS:
            test_true = {k: v[0] for k, v in query_params.items()}
            test_true[param_name] = true_payload
            test_false = {k: v[0] for k, v in query_params.items()}
            test_false[param_name] = false_payload

            url_true = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_true), ""))
            url_false = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_false), ""))

            try:
                resp_true = await http_client.get(url_true)
                resp_false = await http_client.get(url_false)
            except Exception:
                continue

            if resp_true.status_code == 200 and resp_false.status_code != 200:
                return Finding(
                    module_name=self.name,
                    vuln_type="SQL Injection - Boolean Blind",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-89",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=f"Boolean-based blind SQL injection detected in '{param_name}'. True/false conditions produce different responses.",
                    remediation="Use parameterized queries or prepared statements.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "True Condition", "content": true_payload},
                        {"type": "payload", "title": "False Condition", "content": false_payload},
                    ],
                )

            if (abs(len(resp_true.text) - len(resp_false.text)) > 50
                    and resp_true.status_code == resp_false.status_code):
                return Finding(
                    module_name=self.name,
                    vuln_type="SQL Injection - Boolean Blind",
                    severity="high",
                    cvss_score=8.6,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
                    owasp_category="A03",
                    cwe_id="CWE-89",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=f"Possible boolean-blind SQL injection in '{param_name}'. Response size differs significantly between true/false conditions.",
                    remediation="Use parameterized queries or prepared statements.",
                    confidence="tentative",
                    evidence=[
                        {"type": "payload", "title": "True Condition", "content": f"{true_payload} → {len(resp_true.text)} bytes"},
                        {"type": "payload", "title": "False Condition", "content": f"{false_payload} → {len(resp_false.text)} bytes"},
                    ],
                )

        # Time-based detection
        for payload, expected_delay in TIME_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = payload
            test_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""))

            try:
                start = time.monotonic()
                await http_client.get(test_url)
                elapsed = time.monotonic() - start
            except Exception:
                continue

            if elapsed >= expected_delay - 1:
                return Finding(
                    module_name=self.name,
                    vuln_type="SQL Injection - Time Based",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-89",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=f"Time-based SQL injection detected in '{param_name}'. Response delayed by ~{elapsed:.1f}s.",
                    remediation="Use parameterized queries or prepared statements.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "Payload", "content": payload},
                        {"type": "log", "title": "Response Time", "content": f"{elapsed:.2f}s (expected {expected_delay}s)"},
                    ],
                )

        return None

    async def _test_param_form(self, page, form, inp, http_client) -> Finding | None:
        for payload in ERROR_PAYLOADS[:3]:
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

            for pattern in SQL_ERRORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="SQL Injection - Error Based (Form)",
                        severity="critical",
                        cvss_score=9.8,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        owasp_category="A03",
                        cwe_id="CWE-89",
                        affected_url=form.action,
                        affected_parameter=inp["name"],
                        description=f"SQL error detected when injecting into form field '{inp['name']}'.",
                        remediation="Use parameterized queries or prepared statements.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Payload", "content": payload},
                            {"type": "response", "title": "SQL Error", "content": pattern.pattern},
                        ],
                    )
        return None
