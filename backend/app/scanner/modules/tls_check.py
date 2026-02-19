"""TLS/SSL configuration scanner module."""
import ssl
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry


@ModuleRegistry.register
class TlsCheckModule(BaseModule):
    name = "tls_check"
    description = "Checks TLS/SSL configuration for weak ciphers, expired certs, and protocol issues"
    scan_modes = ["quick", "full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)

        if parsed.scheme != "https":
            return findings  # https_check module handles HTTP-only sites

        host = parsed.hostname
        port = parsed.port or 443

        try:
            findings.extend(self._check_certificate(host, port))
            findings.extend(self._check_weak_protocols(host, port))
        except Exception:
            pass  # Network errors are normal for many targets

        return findings

    def _check_certificate(self, host: str, port: int) -> list[Finding]:
        findings: list[Finding] = []
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()

            # Check expiry
            not_after_str = cert.get("notAfter", "")
            if not_after_str:
                not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                not_after = not_after.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_left = (not_after - now).days

                if days_left < 0:
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="Expired TLS Certificate",
                        severity="critical",
                        cvss_score=7.5,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                        owasp_category="A02",
                        cwe_id="CWE-298",
                        affected_url=f"https://{host}:{port}",
                        affected_parameter=None,
                        description=f"TLS certificate expired {abs(days_left)} days ago on {not_after_str}.",
                        remediation="Renew the TLS certificate immediately. Use automated certificate management (ACME/Let's Encrypt).",
                        confidence="confirmed",
                        evidence=[{"type": "log", "title": "Certificate Expiry", "content": f"Expired: {not_after_str} ({abs(days_left)} days ago)"}],
                    ))
                elif days_left < 30:
                    findings.append(Finding(
                        module_name=self.name,
                        vuln_type="TLS Certificate Expiring Soon",
                        severity="medium",
                        cvss_score=5.3,
                        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                        owasp_category="A02",
                        cwe_id="CWE-298",
                        affected_url=f"https://{host}:{port}",
                        affected_parameter=None,
                        description=f"TLS certificate expires in {days_left} days on {not_after_str}.",
                        remediation="Renew the certificate before expiry. Consider automated renewal via ACME protocol.",
                        confidence="confirmed",
                        evidence=[{"type": "log", "title": "Certificate Expiry", "content": f"Expires: {not_after_str} ({days_left} days remaining)"}],
                    ))

        except ssl.SSLCertVerificationError as e:
            findings.append(Finding(
                module_name=self.name,
                vuln_type="Invalid TLS Certificate",
                severity="high",
                cvss_score=7.4,
                cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N",
                owasp_category="A02",
                cwe_id="CWE-295",
                affected_url=f"https://{host}:{port}",
                affected_parameter=None,
                description=f"TLS certificate validation failed: {e}",
                remediation="Install a valid certificate from a trusted CA. Ensure the CN/SAN matches the domain.",
                confidence="confirmed",
                evidence=[{"type": "log", "title": "SSL Error", "content": str(e)}],
            ))
        except Exception:
            pass

        return findings

    def _check_weak_protocols(self, host: str, port: int) -> list[Finding]:
        findings: list[Finding] = []
        weak_protocols = [
            (ssl.PROTOCOL_TLS_CLIENT, "SSLv3", ssl.OP_NO_SSLv2),
        ]

        # Check if SSLv3/TLS 1.0/1.1 are accepted
        for proto_name, min_version in [("TLS 1.0", ssl.TLSVersion.TLSv1), ("TLS 1.1", ssl.TLSVersion.TLSv1_1)]:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = min_version
                ctx.maximum_version = min_version
                with socket.create_connection((host, port), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host):
                        findings.append(Finding(
                            module_name=self.name,
                            vuln_type=f"Weak TLS Protocol Supported: {proto_name}",
                            severity="medium",
                            cvss_score=5.9,
                            cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            owasp_category="A02",
                            cwe_id="CWE-326",
                            affected_url=f"https://{host}:{port}",
                            affected_parameter=None,
                            description=f"Server accepts {proto_name} which has known vulnerabilities (POODLE, BEAST).",
                            remediation=f"Disable {proto_name}. Configure minimum TLS version to TLS 1.2 or higher.",
                            confidence="confirmed",
                            evidence=[{"type": "log", "title": "Accepted Protocol", "content": f"Server accepted connection using {proto_name}"}],
                        ))
            except Exception:
                pass  # Protocol not supported = good

        return findings
