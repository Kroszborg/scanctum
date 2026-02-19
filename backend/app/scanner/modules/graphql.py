"""GraphQL misconfiguration and introspection scanner module."""
import json
import re
from urllib.parse import urlparse, urljoin

from app.scanner.crawler import CrawledPage
from app.scanner.http_client import HttpClient
from app.scanner.modules.base import BaseModule, Finding
from app.scanner.modules.registry import ModuleRegistry

# Common GraphQL endpoint paths to probe
GRAPHQL_PATHS = [
    "/graphql",
    "/graphiql",
    "/graphql/console",
    "/api/graphql",
    "/v1/graphql",
    "/v2/graphql",
    "/query",
    "/gql",
]

INTROSPECTION_QUERY = json.dumps({
    "query": "{ __schema { queryType { name } types { name } } }"
})

BATCH_QUERY = json.dumps([
    {"query": "{ __typename }"},
    {"query": "{ __typename }"},
    {"query": "{ __typename }"},
    {"query": "{ __typename }"},
    {"query": "{ __typename }"},
])

INTROSPECTION_PATTERN = re.compile(r'"__schema"', re.I)
BATCH_SUCCESS_PATTERN = re.compile(r'"__typename"', re.I)


@ModuleRegistry.register
class GraphQLModule(BaseModule):
    name = "graphql"
    description = "Detects GraphQL endpoints with introspection enabled and batching vulnerabilities"
    scan_modes = ["full"]
    is_active = True

    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        findings: list[Finding] = []
        parsed = urlparse(page.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        probed: set[str] = set()

        # Check if current page is already a GraphQL endpoint
        endpoints_to_test = []
        for path in GRAPHQL_PATHS:
            url = urljoin(base_url, path)
            if url not in probed:
                probed.add(url)
                endpoints_to_test.append(url)

        for endpoint in endpoints_to_test:
            introspection_finding = await self._test_introspection(endpoint, http_client)
            if introspection_finding:
                findings.append(introspection_finding)

                # Also test query batching on confirmed GraphQL endpoints
                batching_finding = await self._test_batching(endpoint, http_client)
                if batching_finding:
                    findings.append(batching_finding)

                # Check for GraphiQL IDE exposed
                graphiql_finding = await self._test_graphiql(endpoint, http_client, base_url)
                if graphiql_finding:
                    findings.append(graphiql_finding)

                break  # One endpoint per host is enough for core checks

        return findings

    async def _test_introspection(self, endpoint: str, http_client: HttpClient) -> Finding | None:
        try:
            response = await http_client.client.post(
                endpoint,
                content=INTROSPECTION_QUERY,
                headers={"Content-Type": "application/json"},
            )
        except Exception:
            return None

        if response.status_code == 200 and INTROSPECTION_PATTERN.search(response.text):
            try:
                data = response.json()
                types = data.get("data", {}).get("__schema", {}).get("types", [])
                type_names = [t["name"] for t in types[:5] if t.get("name")]
                type_preview = ", ".join(type_names)
            except Exception:
                type_preview = ""

            return Finding(
                module_name=self.name,
                vuln_type="GraphQL Introspection Enabled",
                severity="medium",
                cvss_score=5.3,
                cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                owasp_category="A05",
                cwe_id="CWE-200",
                affected_url=endpoint,
                affected_parameter=None,
                description=(
                    "GraphQL introspection is enabled, exposing the full API schema. "
                    "Attackers can enumerate all types, queries, mutations, and fields."
                ),
                remediation=(
                    "Disable introspection in production. "
                    "Use field-level authorization and query depth limiting."
                ),
                confidence="confirmed",
                evidence=[
                    {"type": "request", "title": "Introspection Query", "content": INTROSPECTION_QUERY},
                    {"type": "response", "title": "Exposed Types", "content": f"Types found: {type_preview}..."},
                ],
            )
        return None

    async def _test_batching(self, endpoint: str, http_client: HttpClient) -> Finding | None:
        try:
            response = await http_client.client.post(
                endpoint,
                content=BATCH_QUERY,
                headers={"Content-Type": "application/json"},
            )
        except Exception:
            return None

        if response.status_code == 200 and BATCH_SUCCESS_PATTERN.search(response.text):
            try:
                data = response.json()
                count = len(data) if isinstance(data, list) else 0
            except Exception:
                count = 0

            if count >= 3:
                return Finding(
                    module_name=self.name,
                    vuln_type="GraphQL Query Batching Enabled",
                    severity="medium",
                    cvss_score=5.3,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A06",
                    cwe_id="CWE-770",
                    affected_url=endpoint,
                    affected_parameter=None,
                    description=(
                        "GraphQL query batching is enabled. Attackers can send multiple queries "
                        "in a single request to bypass rate limits or amplify attacks."
                    ),
                    remediation="Disable query batching or limit batch size to 1-5 queries. Implement query cost analysis.",
                    confidence="confirmed",
                    evidence=[
                        {"type": "payload", "title": "Batch Query", "content": f"Sent 5 queries, received {count} responses"},
                    ],
                )
        return None

    async def _test_graphiql(self, graphql_endpoint: str, http_client: HttpClient, base_url: str) -> Finding | None:
        graphiql_paths = ["/graphiql", "/graphql/console", "/graphql/voyager"]
        for path in graphiql_paths:
            url = urljoin(base_url, path)
            try:
                response = await http_client.get(url)
            except Exception:
                continue

            if response.status_code == 200 and (
                "graphiql" in response.text.lower()
                or "GraphQL IDE" in response.text
                or "voyager" in response.text.lower()
            ):
                return Finding(
                    module_name=self.name,
                    vuln_type="GraphQL IDE Exposed",
                    severity="medium",
                    cvss_score=5.3,
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
                    owasp_category="A05",
                    cwe_id="CWE-200",
                    affected_url=url,
                    affected_parameter=None,
                    description="GraphQL IDE (GraphiQL/Voyager) is publicly accessible, enabling attackers to explore and test the API interactively.",
                    remediation="Disable GraphQL IDE in production or restrict access to authenticated internal users.",
                    confidence="confirmed",
                    evidence=[{"type": "response", "title": "IDE Response", "content": f"HTTP 200 at {url} with GraphQL IDE content"}],
                )
        return None
