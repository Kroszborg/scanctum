import json
from urllib.parse import urljoin

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

API_ENDPOINTS = [
    "/api/", "/api/v1/", "/api/v2/",
    "/graphql", "/graphiql",
    "/swagger.json", "/openapi.json",
    "/api-docs", "/swagger-ui.html",
    "/_debug/", "/__debug__/",
]


@ModuleRegistry.register
class ApiMisconfigModule(BaseModule):
    name = "api_misconfig"
    description = "Checks for API misconfigurations and exposed documentation"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        base = page.url

        for endpoint in API_ENDPOINTS:
            test_url = urljoin(base, endpoint)
            try:
                response = await http_client.get(test_url)
            except Exception:
                continue

            if response.status_code != 200:
                continue

            # Check for exposed API documentation
            if endpoint in ("/swagger.json", "/openapi.json"):
                try:
                    data = response.json()
                    if "paths" in data or "openapi" in data or "swagger" in data:
                        findings.append(Finding(
                            module_name=self.name,
                            vuln_type="Exposed API Documentation",
                            severity="medium",
                            cvss_score=5.3,
                            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                            owasp_category="A05",
                            cwe_id="CWE-200",
                            affected_url=test_url,
                            affected_parameter=None,
                            description=f"API specification exposed at '{endpoint}'. Attackers can enumerate all endpoints.",
                            remediation="Restrict API documentation to authenticated users only in production.",
                            confidence="confirmed",
                            evidence=[{
                                "type": "response",
                                "title": "API Spec Preview",
                                "content": json.dumps(data, indent=2)[:500],
                            }],
                        ))
                except Exception:
                    pass

            # Check for GraphQL introspection
            if endpoint in ("/graphql", "/graphiql"):
                try:
                    introspection_resp = await http_client.post(
                        test_url,
                        json={"query": "{__schema{types{name}}}"},
                    )
                    if introspection_resp.status_code == 200:
                        data = introspection_resp.json()
                        if "data" in data and "__schema" in data.get("data", {}):
                            findings.append(Finding(
                                module_name=self.name,
                                vuln_type="GraphQL Introspection Enabled",
                                severity="medium",
                                cvss_score=5.3,
                                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                                owasp_category="A05",
                                cwe_id="CWE-200",
                                affected_url=test_url,
                                affected_parameter=None,
                                description="GraphQL introspection is enabled, exposing the full API schema.",
                                remediation="Disable GraphQL introspection in production.",
                                confidence="confirmed",
                                evidence=[{
                                    "type": "response",
                                    "title": "Introspection Response",
                                    "content": json.dumps(data, indent=2)[:500],
                                }],
                            ))
                except Exception:
                    pass

            # Check for debug endpoints
            if "debug" in endpoint:
                findings.append(Finding(
                    module_name=self.name,
                    vuln_type="Debug Endpoint Exposed",
                    severity="high",
                    cvss_score=7.5,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-215",
                    affected_url=test_url,
                    affected_parameter=None,
                    description=f"Debug endpoint accessible at '{endpoint}'.",
                    remediation="Disable debug endpoints in production environments.",
                    confidence="firm",
                    evidence=[{
                        "type": "response",
                        "title": "Response Preview",
                        "content": response.text[:300],
                    }],
                ))

        return findings
