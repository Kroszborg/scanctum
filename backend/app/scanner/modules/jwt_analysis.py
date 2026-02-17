import base64
import json
import re

from app.scanner.crawler import CrawledPage
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

JWT_PATTERN = re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")

WEAK_ALGORITHMS = {"none", "HS256"}


@ModuleRegistry.register
class JwtAnalysisModule(BaseModule):
    name = "jwt_analysis"
    description = "Analyzes JWT tokens found in responses for weaknesses"
    scan_modes = ["quick", "full"]
    is_active = False

    def detect(self, page: CrawledPage) -> list[Finding]:
        findings: list[Finding] = []

        # Search in response body and headers
        search_text = page.body
        for key, val in page.headers.items():
            search_text += f"\n{val}"

        tokens = JWT_PATTERN.findall(search_text)

        for token in set(tokens):
            try:
                header_b64 = token.split(".")[0]
                # Add padding
                header_b64 += "=" * (4 - len(header_b64) % 4)
                header = json.loads(base64.urlsafe_b64decode(header_b64))
            except Exception:
                continue

            alg = header.get("alg", "")

            if alg.lower() == "none":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="JWT Algorithm None",
                    severity="critical",
                    cvss_score=9.8,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    owasp_category="A02",
                    cwe_id="CWE-327",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="A JWT token uses the 'none' algorithm, allowing signature bypass.",
                    remediation="Enforce a strong algorithm (RS256 or ES256) and reject 'none' algorithm.",
                    confidence="confirmed",
                    evidence=[{"type": "payload", "title": "JWT Header", "content": json.dumps(header, indent=2)}],
                ))
            elif alg == "HS256":
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="JWT Weak Algorithm (HS256)",
                    severity="low",
                    cvss_score=3.7,
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A02",
                    cwe_id="CWE-327",
                    affected_url=page.url,
                    affected_parameter=None,
                    description="A JWT token uses HS256 (symmetric). Consider RS256/ES256 for better security.",
                    remediation="Use asymmetric algorithms (RS256, ES256) for JWT signing.",
                    confidence="tentative",
                    evidence=[{"type": "payload", "title": "JWT Header", "content": json.dumps(header, indent=2)}],
                ))

        return findings
