"""Unit tests for scanner modules using mock HTTP responses."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from app.scanner.modules.base import Finding
from app.scanner.crawler import CrawledPage, Form, FormInput


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_page(
    url: str = "https://example.com/",
    body: str = "",
    headers: dict | None = None,
    forms: list | None = None,
    status_code: int = 200,
) -> CrawledPage:
    return CrawledPage(
        url=url,
        status_code=status_code,
        headers=headers or {},
        body=body,
        forms=forms or [],
    )


def make_http_client(text: str = "", status_code: int = 200, headers: dict | None = None):
    """Return a mock HttpClient where every GET/POST returns the given response."""
    response = MagicMock()
    response.text = text
    response.status_code = status_code
    response.headers = headers or {}

    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    client.post = AsyncMock(return_value=response)
    # client.client.request is used by some modules
    client.client = MagicMock()
    client.client.request = AsyncMock(return_value=response)
    client.client.post = AsyncMock(return_value=response)
    return client


# ── Security Headers ──────────────────────────────────────────────────────────

class TestSecurityHeaders:
    def test_missing_hsts_flagged(self):
        from app.scanner.modules.security_headers import SecurityHeadersModule
        module = SecurityHeadersModule()
        page = make_page(url="https://example.com/", headers={
            "content-security-policy": "default-src 'self'",
            "x-frame-options": "DENY",
        })
        findings = module.detect(page)
        types = [f.vuln_type for f in findings]
        assert any("HSTS" in t for t in types)

    def test_missing_csp_flagged(self):
        from app.scanner.modules.security_headers import SecurityHeadersModule
        module = SecurityHeadersModule()
        page = make_page(url="https://example.com/", headers={
            "strict-transport-security": "max-age=31536000",
            "x-frame-options": "DENY",
        })
        findings = module.detect(page)
        types = [f.vuln_type for f in findings]
        assert any("Content-Security-Policy" in t for t in types)

    def test_all_headers_present_no_findings(self):
        from app.scanner.modules.security_headers import SecurityHeadersModule
        module = SecurityHeadersModule()
        page = make_page(url="https://example.com/", headers={
            "strict-transport-security": "max-age=31536000; includeSubDomains",
            "content-security-policy": "default-src 'self'",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "referrer-policy": "no-referrer",
            "permissions-policy": "camera=()",
        })
        findings = module.detect(page)
        assert len(findings) == 0


# ── XSS Module ────────────────────────────────────────────────────────────────

class TestXssModule:
    @pytest.mark.asyncio
    async def test_reflected_xss_detected(self):
        from app.scanner.modules.xss import XssModule, XSS_CANARY
        module = XssModule()
        page = make_page(url="https://example.com/search?q=test")
        # Baseline: normal response
        baseline_resp = MagicMock()
        baseline_resp.text = "Normal response without canary"
        baseline_resp.status_code = 200

        # Reflected response: canary appears unencoded
        reflected_payload = f'<script>{XSS_CANARY}()</script>'
        reflected_resp = MagicMock()
        reflected_resp.text = f"<html><body>{reflected_payload}</body></html>"
        reflected_resp.status_code = 200

        client = make_http_client()
        client.get = AsyncMock(side_effect=[baseline_resp, reflected_resp])

        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert any("XSS" in f.vuln_type for f in findings)
        assert all(f.severity in ("high", "medium", "critical") for f in findings)

    @pytest.mark.asyncio
    async def test_no_xss_when_encoded(self):
        from app.scanner.modules.xss import XssModule, XSS_CANARY
        module = XssModule()
        page = make_page(url="https://example.com/search?q=test")

        # All responses HTML-encode the payload
        resp = MagicMock()
        resp.text = f"&lt;script&gt;{XSS_CANARY}()&lt;/script&gt;"
        resp.status_code = 200
        client = make_http_client()
        client.get = AsyncMock(return_value=resp)

        findings = await module.active_test_async(page, client)
        # Encoded reflection should NOT be flagged as confirmed XSS
        confirmed = [f for f in findings if f.confidence == "confirmed"]
        assert len(confirmed) == 0

    @pytest.mark.asyncio
    async def test_no_url_params_no_active_test(self):
        from app.scanner.modules.xss import XssModule
        module = XssModule()
        page = make_page(url="https://example.com/")
        client = make_http_client()

        findings = await module.active_test_async(page, client)
        # No params → no confirmed XSS findings
        confirmed = [f for f in findings if f.confidence == "confirmed"]
        assert len(confirmed) == 0


# ── SQLi Module ───────────────────────────────────────────────────────────────

class TestSqliModule:
    @pytest.mark.asyncio
    async def test_mysql_error_detected(self):
        from app.scanner.modules.sqli import SqliModule
        module = SqliModule()
        page = make_page(url="https://example.com/item?id=1")
        client = make_http_client(
            text="You have an error in your SQL syntax near '' at line 1"
        )
        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert "MySQL" in findings[0].vuln_type
        assert findings[0].severity == "critical"
        assert findings[0].cwe_id == "CWE-89"

    @pytest.mark.asyncio
    async def test_postgresql_error_detected(self):
        from app.scanner.modules.sqli import SqliModule
        module = SqliModule()
        page = make_page(url="https://example.com/user?id=1")
        client = make_http_client(
            text="org.postgresql.util.PSQLException: ERROR: syntax error at or near"
        )
        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert "PostgreSQL" in findings[0].vuln_type

    @pytest.mark.asyncio
    async def test_clean_response_no_finding(self):
        from app.scanner.modules.sqli import SqliModule
        module = SqliModule()
        page = make_page(url="https://example.com/search?q=hello")
        client = make_http_client(text="<html><body>Results for hello</body></html>")
        findings = await module.active_test_async(page, client)
        assert len(findings) == 0

    @pytest.mark.asyncio
    async def test_no_params_no_test(self):
        from app.scanner.modules.sqli import SqliModule
        module = SqliModule()
        page = make_page(url="https://example.com/about")
        client = make_http_client()
        findings = await module.active_test_async(page, client)
        assert len(findings) == 0


# ── SSRF Module ───────────────────────────────────────────────────────────────

class TestSsrfModule:
    @pytest.mark.asyncio
    async def test_aws_metadata_indicator_detected(self):
        from app.scanner.modules.ssrf import SsrfModule
        module = SsrfModule()
        page = make_page(url="https://example.com/fetch?url=http://test.com")
        client = make_http_client(text="ami-id: ami-12345678")
        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert findings[0].cwe_id == "CWE-918"

    @pytest.mark.asyncio
    async def test_non_ssrf_param_ignored(self):
        from app.scanner.modules.ssrf import SsrfModule
        module = SsrfModule()
        # 'query' is not in URL_PARAMS set
        page = make_page(url="https://example.com/search?query=hello")
        client = make_http_client(text="root:/bin/bash")
        findings = await module.active_test_async(page, client)
        assert len(findings) == 0


# ── CORS Module ───────────────────────────────────────────────────────────────

class TestCorsModule:
    @pytest.mark.asyncio
    async def test_origin_reflection_with_credentials_critical(self):
        from app.scanner.modules.cors import CorsModule
        module = CorsModule()
        page = make_page(url="https://example.com/api/data")

        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {
            "access-control-allow-origin": "https://evil.com",
            "access-control-allow-credentials": "true",
        }

        client = MagicMock()
        client.client = MagicMock()
        client.client.request = AsyncMock(return_value=resp)

        findings = await module.active_test_async(page, client)
        critical = [f for f in findings if f.severity == "critical"]
        assert len(critical) >= 1

    @pytest.mark.asyncio
    async def test_null_origin_allowed(self):
        from app.scanner.modules.cors import CorsModule
        module = CorsModule()
        page = make_page(url="https://example.com/api/data")

        def make_response(origin: str):
            resp = MagicMock()
            resp.status_code = 200
            if origin == "null":
                resp.headers = {"access-control-allow-origin": "null", "access-control-allow-credentials": ""}
            else:
                resp.headers = {"access-control-allow-origin": "", "access-control-allow-credentials": ""}
            return resp

        client = MagicMock()
        client.client = MagicMock()
        client.client.request = AsyncMock(side_effect=lambda method, url, headers: make_response(headers.get("Origin", "")))

        findings = await module.active_test_async(page, client)
        null_findings = [f for f in findings if "Null" in f.vuln_type]
        assert len(null_findings) >= 1

    @pytest.mark.asyncio
    async def test_no_cors_header_no_finding(self):
        from app.scanner.modules.cors import CorsModule
        module = CorsModule()
        page = make_page(url="https://example.com/api/data")

        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {}  # No CORS headers

        client = MagicMock()
        client.client = MagicMock()
        client.client.request = AsyncMock(return_value=resp)

        findings = await module.active_test_async(page, client)
        assert len(findings) == 0


# ── SSTI Module ───────────────────────────────────────────────────────────────

class TestSstiModule:
    @pytest.mark.asyncio
    async def test_math_evaluated_detected(self):
        from app.scanner.modules.ssti import SstiModule
        module = SstiModule()
        page = make_page(url="https://example.com/render?template=hello")

        def response_for(text):
            r = MagicMock()
            r.text = text
            r.status_code = 200
            return r

        baseline = response_for("Normal content")
        evaluated = response_for("The result is 49 and that is correct")

        client = MagicMock()
        client.get = AsyncMock(side_effect=[baseline, evaluated])
        client.client = MagicMock()

        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert findings[0].severity == "critical"

    @pytest.mark.asyncio
    async def test_literal_expression_not_evaluated(self):
        from app.scanner.modules.ssti import SstiModule
        module = SstiModule()
        page = make_page(url="https://example.com/render?template=hello")

        # Response echoes the raw expression — not evaluated
        resp = MagicMock()
        resp.text = "{{7*7}} is the template"  # raw expression echoed back
        resp.status_code = 200

        client = MagicMock()
        client.get = AsyncMock(return_value=resp)

        findings = await module.active_test_async(page, client)
        confirmed = [f for f in findings if f.confidence == "confirmed"]
        assert len(confirmed) == 0


# ── Path Traversal ────────────────────────────────────────────────────────────

class TestPathTraversalModule:
    @pytest.mark.asyncio
    async def test_etc_passwd_disclosed(self):
        from app.scanner.modules.path_traversal import PathTraversalModule
        module = PathTraversalModule()
        page = make_page(url="https://example.com/read?file=readme.txt")
        client = make_http_client(text="root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:")
        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert findings[0].cwe_id == "CWE-22"

    @pytest.mark.asyncio
    async def test_non_file_param_ignored(self):
        from app.scanner.modules.path_traversal import PathTraversalModule
        module = PathTraversalModule()
        # 'q' is not in FILE_PARAMS
        page = make_page(url="https://example.com/search?q=test")
        client = make_http_client(text="root:x:0:0:root:/root:/bin/bash")
        findings = await module.active_test_async(page, client)
        assert len(findings) == 0


# ── Command Injection ─────────────────────────────────────────────────────────

class TestCommandInjectionModule:
    @pytest.mark.asyncio
    async def test_canary_in_response_detected(self):
        from app.scanner.modules.command_injection import CommandInjectionModule, CANARY
        module = CommandInjectionModule()
        page = make_page(url="https://example.com/ping?host=example.com")
        client = make_http_client(text=f"PING output\n{CANARY}\nend")
        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert findings[0].severity == "critical"
        assert findings[0].cwe_id == "CWE-78"


# ── CRLF Injection ────────────────────────────────────────────────────────────

class TestCrlfInjectionModule:
    @pytest.mark.asyncio
    async def test_injected_header_detected(self):
        from app.scanner.modules.crlf_injection import CrlfInjectionModule, CRLF_HEADER_NAME
        module = CrlfInjectionModule()
        page = make_page(url="https://example.com/redirect?url=https://example.com")

        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {CRLF_HEADER_NAME.lower(): "injected"}
        resp.text = ""

        client = MagicMock()
        client.get = AsyncMock(return_value=resp)

        findings = await module.active_test_async(page, client)
        assert len(findings) >= 1
        assert "CRLF" in findings[0].vuln_type


# ── GraphQL Module ────────────────────────────────────────────────────────────

class TestGraphQLModule:
    @pytest.mark.asyncio
    async def test_introspection_enabled_detected(self):
        from app.scanner.modules.graphql import GraphQLModule
        module = GraphQLModule()
        page = make_page(url="https://example.com/")

        introspection_resp = MagicMock()
        introspection_resp.status_code = 200
        introspection_resp.text = '{"data": {"__schema": {"queryType": {"name": "Query"}, "types": [{"name": "User"}, {"name": "Query"}]}}}'
        introspection_resp.json = lambda: {
            "data": {"__schema": {"queryType": {"name": "Query"}, "types": [{"name": "User"}]}}
        }

        no_resp = MagicMock()
        no_resp.status_code = 404
        no_resp.text = "Not found"

        client = MagicMock()
        client.get = AsyncMock(return_value=no_resp)
        client.client = MagicMock()
        client.client.post = AsyncMock(return_value=introspection_resp)

        findings = await module.active_test_async(page, client)
        introspection_findings = [f for f in findings if "Introspection" in f.vuln_type]
        assert len(introspection_findings) >= 1


# ── Module Registry ───────────────────────────────────────────────────────────

class TestModuleRegistry:
    def test_all_modules_discovered(self):
        from app.scanner.modules.registry import ModuleRegistry
        ModuleRegistry.discover()
        modules = ModuleRegistry.get_all()
        expected_names = {
            "security_headers", "https_check", "cookie_security", "robots_txt",
            "jwt_analysis", "cors", "open_redirect", "xss", "directory_exposure",
            "sqli", "csrf", "ssrf", "idor", "sensitive_files", "api_misconfig",
            "rate_limit_check", "tls_check", "path_traversal", "ssti", "graphql",
            "xxe", "crlf_injection", "command_injection",
        }
        missing = expected_names - set(modules.keys())
        assert not missing, f"Missing modules: {missing}"

    def test_quick_mode_modules_subset(self):
        from app.scanner.modules.registry import ModuleRegistry
        ModuleRegistry.discover()
        quick_modules = {m.name for m in ModuleRegistry.get_for_mode("quick")}
        full_modules = {m.name for m in ModuleRegistry.get_for_mode("full")}
        # All quick modules should also be in full
        assert quick_modules.issubset(full_modules)
        # Full should have more modules
        assert len(full_modules) > len(quick_modules)

    def test_sqli_is_full_only(self):
        from app.scanner.modules.registry import ModuleRegistry
        ModuleRegistry.discover()
        quick = {m.name for m in ModuleRegistry.get_for_mode("quick")}
        full = {m.name for m in ModuleRegistry.get_for_mode("full")}
        assert "sqli" not in quick
        assert "sqli" in full
