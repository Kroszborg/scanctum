"""Ground truth validation for vulnerability scanner evaluation."""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional
import httpx

from app.scanner.modules.base import Finding

logger = logging.getLogger(__name__)


@dataclass
class GroundTruthVulnerability:
    """A known vulnerability in a test application."""
    name: str
    vuln_type: str
    location: str  # URL path or endpoint
    parameter: Optional[str]
    severity: str
    description: str
    cwe_id: str = ""

    def matches_finding(self, finding: Finding) -> bool:
        """Check if a finding matches this ground truth vulnerability."""
        # Match on URL containing location
        if self.location not in finding.affected_url:
            return False
        # Match on vulnerability type (case-insensitive partial match)
        if self.vuln_type.lower() not in finding.vuln_type.lower():
            return False
        # Optional: match parameter if specified
        if self.parameter and self.parameter.lower() != (finding.affected_parameter or "").lower():
            return False
        return True


@dataclass
class ValidationTarget:
    """A target application for validation."""
    name: str
    base_url: str
    ground_truth: list[GroundTruthVulnerability]
    description: str = ""


# DVWA ground truth (Low difficulty)
DVWA_GROUND_TRUTH = [
    # SQL Injection
    GroundTruthVulnerability(
        name="DVWA SQLi - Login Bypass",
        vuln_type="SQL Injection",
        location="/vulnerabilities/sqli/",
        parameter="id",
        severity="critical",
        description="SQL injection in user ID parameter",
        cwe_id="CWE-89",
    ),
    GroundTruthVulnerability(
        name="DVWA SQLi - Search",
        vuln_type="SQL Injection",
        location="/vulnerabilities/sqli/",
        parameter="Search",
        severity="critical",
        description="SQL injection in search field",
        cwe_id="CWE-89",
    ),
    # XSS Reflected
    GroundTruthVulnerability(
        name="DVWA XSS Reflected - Input",
        vuln_type="Reflected XSS",
        location="/vulnerabilities/xss_r/",
        parameter="name",
        severity="high",
        description="Reflected XSS in name parameter",
        cwe_id="CWE-79",
    ),
    # XSS Stored
    GroundTruthVulnerability(
        name="DVWA XSS Stored - Guestbook",
        vuln_type="Stored XSS",
        location="/vulnerabilities/xss_s/",
        parameter="txtName",
        severity="high",
        description="Stored XSS in guestbook",
        cwe_id="CWE-79",
    ),
    # CSRF
    GroundTruthVulnerability(
        name="DVWA CSRF - Password Change",
        vuln_type="CSRF",
        location="/vulnerabilities/csrf/",
        parameter="password_new",
        severity="high",
        description="CSRF in password change",
        cwe_id="CWE-352",
    ),
    # Command Injection
    GroundTruthVulnerability(
        name="DVWA Command Injection",
        vuln_type="Command Injection",
        location="/vulnerabilities/exec/",
        parameter="ip",
        severity="critical",
        description="OS command injection in ping test",
        cwe_id="CWE-78",
    ),
    # Path Traversal
    GroundTruthVulnerability(
        name="DVWA Path Traversal",
        vuln_type="Path Traversal",
        location="/vulnerabilities/fi/",
        parameter="page",
        severity="high",
        description="Local file inclusion vulnerability",
        cwe_id="CWE-22",
    ),
    # Blind SQLi
    GroundTruthVulnerability(
        name="DVWA Blind SQLi",
        vuln_type="SQL Injection",
        location="/vulnerabilities/sqli_blind/",
        parameter="id",
        severity="critical",
        description="Blind SQL injection vulnerability",
        cwe_id="CWE-89",
    ),
]

# OWASP Juice Shop ground truth (subset of known challenges)
JUICE_SHOP_GROUND_TRUTH = [
    GroundTruthVulnerability(
        name="Juice Shop SQLi - Login",
        vuln_type="SQL Injection",
        location="/rest/user/login",
        parameter="email",
        severity="critical",
        description="SQL injection in login email field",
        cwe_id="CWE-89",
    ),
    GroundTruthVulnerability(
        name="Juice Shop XSS - Search",
        vuln_type="XSS",
        location="/",
        parameter="q",
        severity="high",
        description="Reflected XSS in search query",
        cwe_id="CWE-79",
    ),
    GroundTruthVulnerability(
        name="Juice Shop Directory Traversal",
        vuln_type="Path Traversal",
        location="/ftp/",
        parameter="file",
        severity="high",
        description="Directory traversal in FTP endpoint",
        cwe_id="CWE-22",
    ),
    GroundTruthVulnerability(
        name="Juice Shop XXE",
        vuln_type="XXE",
        location="/file-upload",
        parameter="file",
        severity="critical",
        description="XXE in file upload",
        cwe_id="CWE-611",
    ),
]

# WebGoat ground truth (subset)
WEBGOAT_GROUND_TRUTH = [
    GroundTruthVulnerability(
        name="WebGoat SQLi - Assignment",
        vuln_type="SQL Injection",
        location="/WebGoat/SqlInjection",
        parameter="username",
        severity="critical",
        description="SQL injection in login assignment",
        cwe_id="CWE-89",
    ),
    GroundTruthVulnerability(
        name="WebGoat XSS - Assignment",
        vuln_type="XSS",
        location="/WebGoat/CrossSiteScripting",
        parameter="phrase",
        severity="high",
        description="XSS in search phrase",
        cwe_id="CWE-79",
    ),
    GroundTruthVulnerability(
        name="WebGoat Command Injection",
        vuln_type="Command Injection",
        location="/WebGoat/CommandInjection",
        parameter="host",
        severity="critical",
        description="Command injection in ping test",
        cwe_id="CWE-78",
    ),
]


@dataclass
class ValidationMetrics:
    """Metrics from validation run."""
    target_name: str
    true_positives: list = field(default_factory=list)
    false_positives: list = field(default_factory=list)
    false_negatives: list = field(default_factory=list)

    @property
    def tp(self) -> int:
        return len(self.true_positives)

    @property
    def fp(self) -> int:
        return len(self.false_positives)

    @property
    def fn(self) -> int:
        return len(self.false_negatives)

    @property
    def precision(self) -> float:
        if self.tp + self.fp == 0:
            return 0.0
        return self.tp / (self.tp + self.fp)

    @property
    def recall(self) -> float:
        if self.tp + self.fn == 0:
            return 0.0
        return self.tp / (self.tp + self.fn)

    @property
    def f1_score(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    def to_dict(self) -> dict:
        return {
            "target": self.target_name,
            "true_positives": self.tp,
            "false_positives": self.fp,
            "false_negatives": self.fn,
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3),
        }


class ScannerValidator:
    """Validates scanner findings against ground truth."""

    def __init__(self, scanctum_base_url: str = "http://localhost:8000"):
        self.base_url = scanctum_base_url
        self.targets = {
            "dvwa": ValidationTarget(
                name="DVWA",
                base_url="",  # Set at runtime
                ground_truth=DVWA_GROUND_TRUTH,
                description="Damn Vulnerable Web Application (Low difficulty)",
            ),
            "juice_shop": ValidationTarget(
                name="OWASP Juice Shop",
                base_url="",
                ground_truth=JUICE_SHOP_GROUND_TRUTH,
                description="OWASP Juice Shop v15.x",
            ),
            "webgoat": ValidationTarget(
                name="WebGoat",
                base_url="",
                ground_truth=WEBGOAT_GROUND_TRUTH,
                description="OWASP WebGoat 2023.x",
            ),
        }

    def validate_findings(
        self,
        findings: list[Finding],
        ground_truth: list[GroundTruthVulnerability],
    ) -> ValidationMetrics:
        """
        Validate findings against ground truth.

        Returns metrics with TP, FP, FN counts.
        """
        metrics = ValidationMetrics(target_name="unknown")
        matched_ground_truth = set()

        for finding in findings:
            matched = False
            for gt in ground_truth:
                if gt.matches_finding(finding):
                    matched = True
                    matched_ground_truth.add(gt.name)
                    metrics.true_positives.append({
                        "finding": {
                            "vuln_type": finding.vuln_type,
                            "url": finding.affected_url,
                            "confidence": finding.confidence,
                            "category": finding.get_category().value,
                        },
                        "ground_truth": gt.name,
                    })
                    break

            if not matched:
                # Only count exploitable findings as FPs
                category = finding.get_category()
                if category == FindingCategory.EXPLOITABLE:
                    metrics.false_positives.append({
                        "finding": {
                            "vuln_type": finding.vuln_type,
                            "url": finding.affected_url,
                            "confidence": finding.confidence,
                        },
                        "reason": "No matching ground truth vulnerability",
                    })

        # Find false negatives (ground truth not found)
        for gt in ground_truth:
            if gt.name not in matched_ground_truth:
                metrics.false_negatives.append({
                    "ground_truth": gt.name,
                    "reason": "Not detected by scanner",
                })

        return metrics

    async def run_validation_scan(
        self,
        target_name: str,
        target_url: str,
        scan_mode: str = "full",
    ) -> ValidationMetrics:
        """
        Run a scan against a validation target and compute metrics.

        This triggers a scan via the Scanctum API, waits for completion,
        fetches findings, and validates against ground truth.
        """
        if target_name not in self.targets:
            raise ValueError(f"Unknown target: {target_name}")

        target = self.targets[target_name]
        target.base_url = target_url

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: Create scan
            scan_response = await client.post(
                f"{self.base_url}/api/v1/scans",
                json={
                    "target_url": target_url,
                    "scan_mode": scan_mode,
                },
            )
            scan_response.raise_for_status()
            scan_data = scan_response.json()
            scan_id = scan_data["id"]

            logger.info(f"Scan created: {scan_id}")

            # Step 2: Wait for scan to complete (poll every 10 seconds)
            while True:
                await asyncio.sleep(10)
                status_response = await client.get(
                    f"{self.base_url}/api/v1/scans/{scan_id}"
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data.get("status") in ["completed", "failed"]:
                    logger.info(f"Scan completed with status: {status_data['status']}")
                    break

            if status_data.get("status") == "failed":
                logger.error(f"Scan failed: {status_data.get('error_message', 'Unknown error')}")
                return ValidationMetrics(target_name=target_name)

            # Step 3: Fetch findings
            vulns_response = await client.get(
                f"{self.base_url}/api/v1/scans/{scan_id}/vulnerabilities"
            )
            vulns_response.raise_for_status()
            vulns_data = vulns_response.json()

            # Step 4: Convert to Finding objects
            findings = []
            for v in vulns_data.get("vulnerabilities", []):
                finding = Finding(
                    module_name=v.get("module_name", "unknown"),
                    vuln_type=v.get("vuln_type", "Unknown"),
                    severity=v.get("severity", "info"),
                    cvss_score=v.get("cvss_score", 0.0),
                    cvss_vector=v.get("cvss_vector", ""),
                    owasp_category=v.get("owasp_category", ""),
                    cwe_id=v.get("cwe_id", ""),
                    affected_url=v.get("affected_url", ""),
                    affected_parameter=v.get("affected_parameter"),
                    description=v.get("description", ""),
                    remediation=v.get("remediation", ""),
                    confidence=v.get("confidence", "firm"),
                )
                findings.append(finding)

            logger.info(f"Fetched {len(findings)} findings")

            # Step 5: Validate against ground truth
            metrics = self.validate_findings(findings, target.ground_truth)
            metrics.target_name = target_name

            return metrics

    def run_batch_validation(
        self,
        targets: dict[str, str],  # {name: url}
        scan_mode: str = "full",
    ) -> dict[str, ValidationMetrics]:
        """Run validation against multiple targets."""
        results = {}
        for name, url in targets.items():
            logger.info(f"Validating against {name} at {url}")
            metrics = asyncio.run(
                self.run_validation_scan(name, url, scan_mode)
            )
            results[name] = metrics
            logger.info(f"Results for {name}: {metrics.to_dict()}")

        return results


def print_validation_report(results: dict[str, ValidationMetrics]) -> str:
    """Generate a validation report string."""
    lines = [
        "=" * 60,
        "SCANCTUM VALIDATION REPORT",
        "=" * 60,
        "",
    ]

    for target_name, metrics in results.items():
        lines.append(f"Target: {target_name}")
        lines.append("-" * 40)
        lines.append(f"  True Positives:  {metrics.tp}")
        lines.append(f"  False Positives: {metrics.fp}")
        lines.append(f"  False Negatives: {metrics.fn}")
        lines.append(f"  Precision:       {metrics.precision:.1%}")
        lines.append(f"  Recall:          {metrics.recall:.1%}")
        lines.append(f"  F1 Score:        {metrics.f1_score:.1%}")
        lines.append("")

        if metrics.false_positives:
            lines.append("  False Positives:")
            for fp in metrics.false_positives[:5]:  # Show first 5
                lines.append(f"    - {fp['finding']['vuln_type']} at {fp['finding']['url']}")
            if len(metrics.false_positives) > 5:
                lines.append(f"    ... and {len(metrics.false_positives) - 5} more")
            lines.append("")

        if metrics.false_negatives:
            lines.append("  False Negatives (missed):")
            for fn in metrics.false_negatives[:5]:  # Show first 5
                lines.append(f"    - {fn['ground_truth']}")
            if len(metrics.false_negatives) > 5:
                lines.append(f"    ... and {len(metrics.false_negatives) - 5} more")
            lines.append("")

    # Summary
    total_tp = sum(m.tp for m in results.values())
    total_fp = sum(m.fp for m in results.values())
    total_fn = sum(m.fn for m in results.values())

    avg_precision = sum(m.precision for m in results.values()) / len(results) if results else 0
    avg_recall = sum(m.recall for m in results.values()) / len(results) if results else 0
    avg_f1 = sum(m.f1_score for m in results.values()) / len(results) if results else 0

    lines.append("=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    lines.append(f"  Total Targets:       {len(results)}")
    lines.append(f"  Total True Positives:  {total_tp}")
    lines.append(f"  Total False Positives: {total_fp}")
    lines.append(f"  Total False Negatives: {total_fn}")
    lines.append(f"  Average Precision:   {avg_precision:.1%}")
    lines.append(f"  Average Recall:      {avg_recall:.1%}")
    lines.append(f"  Average F1 Score:    {avg_f1:.1%}")
    lines.append("=" * 60)

    return "\n".join(lines)
