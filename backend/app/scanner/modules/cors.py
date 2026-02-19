"""CORS misconfiguration scanner module — includes subdomain and protocol tests."""
from urllib.parse import urlparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


def _build_subdomain_origins(target_url: str) -> list[str]:
    """Generate attacker-controlled subdomain variants of the target's domain."""
    parsed = urlparse(target_url)
    host = parsed.hostname or ""
    scheme = parsed.scheme

    # Strip leading www.
    bare = host.removeprefix("www.")

    return [
        f"{scheme}://evil.{bare}",
        f"{scheme}://attacker.{bare}",
        f"{scheme}://{bare}.evil.com",
        f"https://evil.{bare}",                # HTTPS variant even if target is HTTP
        f"http://evil.{bare}",
        f"null",                                # Sandboxed-iframe attack
        f"{scheme}://{bare}x.com",             # Domain suffix manipulation
        f"{scheme}://sub.evil.com.{bare}",     # Subdomain confusion
    ]


@ModuleRegistry.register
class CorsModule(BaseModule):
    name = "cors"
    description = "Tests for CORS misconfiguration — subdomain, null-origin, and wildcard tests"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []

        # Build the full test-origin list:
        # external evil.com, protocol variants, subdomain attacks
        base_origins = [
            "https://evil.com",
            "http://evil.com",        # HTTP origin against HTTPS endpoint
            "null",                   # Sandboxed iframe
        ]
        subdomain_origins = _build_subdomain_origins(page.url)
        all_origins = list(dict.fromkeys(base_origins + subdomain_origins))  # dedup, preserve order

        for origin in all_origins:
            try:
                response = await http_client.client.request(
                    "GET",
                    page.url,
                    headers={"Origin": origin},
                )
            except Exception:
                continue

            acao = response.headers.get("access-control-allow-origin", "")
            acac = response.headers.get("access-control-allow-credentials", "").lower()
            acam = response.headers.get("access-control-allow-methods", "")

            # ── Case 1: Wildcard + credentials (invalid but some frameworks allow) ──
            if acao == "*" and acac == "true":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Wildcard with Credentials",
                    severity="high",
                    cvss_score=8.1,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=(
                        "CORS is configured to allow any origin (*) with credentials=true. "
                        "This enables any website to read authenticated responses."
                    ),
                    remediation="Never combine ACAO: * with credentials. Whitelist specific trusted origins.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "CORS Headers", "content": f"Access-Control-Allow-Origin: {acao}\nAccess-Control-Allow-Credentials: {acac}"}],
                ))
                break

            # ── Case 2: Arbitrary origin reflected (most dangerous) ──────────
            if origin not in ("null", "*") and acao == origin:
                if acac == "true":
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="CORS Origin Reflection with Credentials",
                        severity="critical",
                        cvss_score=9.1,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:N",
                        owasp_category="A05",
                        cwe_id="CWE-942",
                        affected_url=page.url,
                        affected_parameter=None,
                        description=(
                            f"CORS reflects the attacker-controlled origin '{origin}' with "
                            "credentials=true, enabling full cross-origin data theft including cookies."
                        ),
                        remediation="Validate origins against a strict whitelist. Never reflect the request Origin header.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "request", "title": "Origin Sent", "content": f"Origin: {origin}"},
                            {"type": "response", "title": "CORS Response", "content": f"ACAO: {acao}\nACAC: {acac}\nACAM: {acam}"},
                        ],
                    ))
                else:
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="CORS Origin Reflection (No Credentials)",
                        severity="medium",
                        cvss_score=5.4,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                        owasp_category="A05",
                        cwe_id="CWE-942",
                        affected_url=page.url,
                        affected_parameter=None,
                        description=(
                            f"CORS reflects arbitrary origin '{origin}'. "
                            "Without credentials this allows reading public API responses cross-origin."
                        ),
                        remediation="Validate origins against a strict allowlist instead of reflecting the request Origin.",
                        confidence="confirmed",
                        evidence=[
                            {"type": "request", "title": "Origin Sent", "content": f"Origin: {origin}"},
                            {"type": "response", "title": "CORS Response", "content": f"ACAO: {acao}\nACAC: {acac}"},
                        ],
                    ))
                break  # One finding per page is sufficient

            # ── Case 3: Null origin allowed ───────────────────────────────────
            if origin == "null" and acao == "null":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Null Origin Allowed",
                    severity="medium",
                    cvss_score=5.4,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=(
                        "CORS allows the 'null' origin. Attackers can exploit this via sandboxed iframes "
                        "to make cross-origin requests with the null origin."
                    ),
                    remediation="Do not allowlist 'null' as a valid CORS origin.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "CORS Headers", "content": f"Access-Control-Allow-Origin: {acao}"}],
                ))
                break

            # ── Case 4: Subdomain wildcard misuse ─────────────────────────────
            if "evil." in origin and acao == origin:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="CORS Subdomain Origin Accepted",
                    severity="high",
                    cvss_score=7.4,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-942",
                    affected_url=page.url,
                    affected_parameter=None,
                    description=(
                        f"CORS reflects subdomain origin '{origin}'. "
                        "If an attacker controls any subdomain (e.g., via subdomain takeover), "
                        "they can read authenticated responses."
                    ),
                    remediation="Restrict CORS to exact trusted origins only. Audit all subdomains for takeover risks.",
                    confidence="confirmed",
                    evidence=[
                        {"type": "request", "title": "Subdomain Origin", "content": f"Origin: {origin}"},
                        {"type": "response", "title": "CORS Response", "content": f"ACAO: {acao}\nACAC: {acac}"},
                    ],
                ))
                break

        return findings
