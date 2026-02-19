"""Path traversal (directory traversal) scanner module."""
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Params likely to contain file paths
FILE_PARAMS = {"file", "path", "page", "template", "view", "doc", "document",
               "include", "dir", "folder", "name", "filename", "load", "read",
               "data", "content", "src", "source", "img", "image"}

TRAVERSAL_PAYLOADS = [
    "../../../../etc/passwd",
    "..%2F..%2F..%2F..%2Fetc%2Fpasswd",
    "....//....//....//....//etc/passwd",
    "..%252F..%252F..%252F..%252Fetc%252Fpasswd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "../../../../etc/shadow",
    "../../../../windows/win.ini",
    "..%2F..%2F..%2F..%2Fwindows%2Fwin.ini",
    "../../../../proc/self/environ",
    "/etc/passwd",
    "/etc/hosts",
]

TRAVERSAL_INDICATORS = [
    re.compile(r"root:.*:/bin/", re.I),             # /etc/passwd
    re.compile(r"\[extensions\]", re.I),             # win.ini
    re.compile(r"for 16-bit app support", re.I),     # win.ini
    re.compile(r"daemon:.*:/usr/sbin", re.I),        # /etc/passwd
    re.compile(r"HOME=/", re.I),                     # /proc/self/environ
]


@ModuleRegistry.register
class PathTraversalModule(BaseModule):
    name = "path_traversal"
    description = "Tests for path traversal / directory traversal vulnerabilities"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        for param_name in query_params:
            if param_name.lower() not in FILE_PARAMS:
                continue

            finding = await self._test_param(page, param_name, query_params, parsed, http_client)
            if finding:
                findings.append(finding)
                break  # One finding per page is sufficient

        # Also test forms
        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name") or inp["name"].lower() not in FILE_PARAMS:
                    continue
                finding = await self._test_form_input(form, inp, http_client)
                if finding:
                    findings.append(finding)
                    break

        return findings

    async def _test_param(self, page, param_name, query_params, parsed, http_client) -> Finding | None:
        for payload in TRAVERSAL_PAYLOADS:
            test_params = {k: v[0] for k, v in query_params.items()}
            test_params[param_name] = payload
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), ""
            ))
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            for pattern in TRAVERSAL_INDICATORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="Path Traversal",
                        severity="high",
                        cvss_score=7.5,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                        owasp_category="A01",
                        cwe_id="CWE-22",
                        affected_url=page.url,
                        affected_parameter=param_name,
                        description=f"Parameter '{param_name}' is vulnerable to path traversal. Sensitive file content was disclosed.",
                        remediation="Validate and canonicalize file paths. Use an allowlist of permitted files. Never construct file paths from user input.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Traversal Payload", "content": payload},
                            {"type": "request", "title": "Test URL", "content": test_url},
                            {"type": "response", "title": "File Content Match", "content": self._extract_match(response.text, pattern)},
                        ],
                    )
        return None

    async def _test_form_input(self, form, inp, http_client) -> Finding | None:
        for payload in TRAVERSAL_PAYLOADS[:4]:
            data = {i["name"]: i.get("value", "test") for i in form.inputs if i.get("name")}
            data[inp["name"]] = payload
            try:
                if form.method == "POST":
                    response = await http_client.post(form.action, data=data)
                else:
                    from urllib.parse import urlencode
                    test_url = f"{form.action}?{urlencode(data)}"
                    response = await http_client.get(test_url)
            except Exception:
                continue

            for pattern in TRAVERSAL_INDICATORS:
                if pattern.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="Path Traversal (Form)",
                        severity="high",
                        cvss_score=7.5,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                        owasp_category="A01",
                        cwe_id="CWE-22",
                        affected_url=form.action,
                        affected_parameter=inp["name"],
                        description=f"Form field '{inp['name']}' is vulnerable to path traversal.",
                        remediation="Validate file paths server-side. Use allowlists and canonicalization.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "Traversal Payload", "content": payload},
                            {"type": "response", "title": "File Content Match", "content": self._extract_match(response.text, pattern)},
                        ],
                    )
        return None

    @staticmethod
    def _extract_match(text: str, pattern: re.Pattern, context: int = 100) -> str:
        m = pattern.search(text)
        if not m:
            return ""
        start = max(0, m.start() - context)
        end = min(len(text), m.end() + context)
        return f"...{text[start:end]}..."
