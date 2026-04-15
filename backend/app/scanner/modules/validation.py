"""Confidence scoring and validation utilities for vulnerability findings."""
import re
from typing import Optional
from dataclasses import dataclass

from .base import Finding


@dataclass
class ConfidenceFactors:
    """Factors that contribute to finding confidence."""
    error_pattern_match: bool = False      # DB error or specific error found
    time_delay_match: bool = False         # Timing-based confirmation
    boolean_difference: bool = False       # True/false response differs
    multiple_payloads_success: bool = False  # 2+ payloads worked
    data_extraction: bool = False          # Actually extracted sensitive data
    waf_detected: bool = False             # WAF may cause false positive
    oob_callback: bool = False             # Out-of-band confirmation

    def calculate_score(self) -> float:
        """Calculate confidence score 0.0 - 1.0."""
        score = 0.0

        if self.error_pattern_match:
            score += 0.25
        if self.time_delay_match:
            score += 0.20
        if self.boolean_difference:
            score += 0.20
        if self.multiple_payloads_success:
            score += 0.15
        if self.data_extraction:
            score += 0.20
        if self.oob_callback:
            score += 0.15

        # Penalty for WAF presence (increases FP risk)
        if self.waf_detected:
            score = min(score, 0.5)  # Cap at 0.5 if WAF detected

        return min(score, 1.0)

    def get_confidence_label(self) -> str:
        """Convert score to confidence label."""
        score = self.calculate_score()
        if score >= 0.7:
            return "confirmed"
        elif score >= 0.5:
            return "firm"
        elif score >= 0.3:
            return "tentative"
        else:
            return "low"


# WAF/Security appliance detection signatures
WAF_SIGNATURES = [
    re.compile(r"blocked\s*this\s*request", re.I),
    re.compile(r"security\s*(appliance|firewall|gatewa)", re.I),
    re.compile(r"incident\s*id[:\s]", re.I),
    re.compile(r"cloudflare", re.I),
    re.compile(r"akamai", re.I),
    re.compile(r"aws\s*shield", re.I),
    re.compile(r"mod_security", re.I),
    re.compile(r"access\s*denied", re.I),
    re.compile(r"forbidden\s*by\s*rule", re.I),
    re.compile(r"request\s*blocked", re.I),
]


def detect_waf(response_text: str) -> bool:
    """Detect if response indicates WAF/security appliance blocking."""
    return any(sig.search(response_text) for sig in WAF_SIGNATURES)


def calculate_cvss_adjusted(
    base_score: float,
    data_extraction: bool = False,
    multiple_vectors: bool = False,
    authentication_required: bool = False,
) -> float:
    """
    Adjust CVSS score based on actual exploitation evidence.

    Args:
        base_score: Base CVSS score from vulnerability type
        data_extraction: Whether actual data was extracted
        multiple_vectors: Whether multiple attack vectors worked
        authentication_required: Whether auth is needed for exploit

    Returns:
        Adjusted CVSS score (rounded to 1 decimal)
    """
    adjusted = base_score

    # Increase if data was actually extracted
    if data_extraction:
        adjusted = min(adjusted + 0.5, 10.0)

    # Increase if multiple exploitation methods worked
    if multiple_vectors:
        adjusted = min(adjusted + 0.3, 10.0)

    # Decrease if authentication is required (lower accessibility)
    if authentication_required:
        adjusted = max(adjusted - 0.5, 0.0)

    return round(adjusted, 1)


def create_validated_finding(
    module_name: str,
    vuln_type: str,
    base_severity: str,
    base_cvss: float,
    base_cvss_vector: str,
    owasp_category: str,
    cwe_id: str,
    affected_url: str,
    affected_parameter: Optional[str],
    description: str,
    remediation: str,
    confidence_factors: ConfidenceFactors,
    evidence: list[dict],
    data_extraction: bool = False,
) -> Finding:
    """
    Create a Finding with calculated confidence and adjusted CVSS.

    This replaces hardcoded confidence/CVSS with dynamically calculated values.
    """
    confidence = confidence_factors.get_confidence_label()
    cvss_score = calculate_cvss_adjusted(
        base_cvss,
        data_extraction=data_extraction,
        multiple_vectors=confidence_factors.multiple_payloads_success,
    )

    return Finding(
        module_name=module_name,
        vuln_type=vuln_type,
        severity=base_severity,
        cvss_score=cvss_score,
        cvss_vector=base_cvss_vector,
        owasp_category=owasp_category,
        cwe_id=cwe_id,
        affected_url=affected_url,
        affected_parameter=affected_parameter,
        description=description,
        remediation=remediation,
        confidence=confidence,
        evidence=evidence,
    )


# Ground truth validation for known vulnerable applications
@dataclass
class GroundTruthVulnerability:
    """A known vulnerability in a test application."""
    name: str
    vuln_type: str
    location: str  # URL or endpoint
    parameter: Optional[str]
    severity: str
    description: str

    def matches_finding(self, finding: Finding) -> bool:
        """Check if a finding matches this ground truth vulnerability."""
        # Match on URL and vulnerability type
        if self.location not in finding.affected_url:
            return False
        if self.vuln_type.lower() not in finding.vuln_type.lower():
            return False
        # Optional: match parameter if specified
        if self.parameter and self.parameter.lower() != (finding.affected_parameter or "").lower():
            return False
        return True


# DVWA ground truth (Low difficulty)
DVWA_GROUND_TRUTH = [
    # SQL Injection (8 instances)
    GroundTruthVulnerability(
        name="DVWA SQLi - Login Bypass",
        vuln_type="SQL Injection",
        location="/vulnerabilities/sqli/",
        parameter="id",
        severity="critical",
        description="SQL injection in user ID parameter",
    ),
    GroundTruthVulnerability(
        name="DVWA SQLi - Search",
        vuln_type="SQL Injection",
        location="/vulnerabilities/sqli/",
        parameter="Search",
        severity="critical",
        description="SQL injection in search field",
    ),
    # XSS Reflected (4 instances)
    GroundTruthVulnerability(
        name="DVWA XSS Reflected - Input",
        vuln_type="Reflected XSS",
        location="/vulnerabilities/xss_r/",
        parameter="name",
        severity="high",
        description="Reflected XSS in name parameter",
    ),
    # XSS Stored (2 instances)
    GroundTruthVulnerability(
        name="DVWA XSS Stored - Guestbook",
        vuln_type="Stored XSS",
        location="/vulnerabilities/xss_s/",
        parameter="txtName",
        severity="high",
        description="Stored XSS in guestbook",
    ),
    # CSRF (2 instances)
    GroundTruthVulnerability(
        name="DVWA CSRF - Password Change",
        vuln_type="CSRF",
        location="/vulnerabilities/csrf/",
        parameter="password_new",
        severity="high",
        description="CSRF in password change",
    ),
    # Command Injection (4 instances)
    GroundTruthVulnerability(
        name="DVWA Command Injection",
        vuln_type="Command Injection",
        location="/vulnerabilities/exec/",
        parameter="ip",
        severity="critical",
        description="OS command injection in ping test",
    ),
    # Path Traversal (4 instances)
    GroundTruthVulnerability(
        name="DVWA Path Traversal",
        vuln_type="Path Traversal",
        location="/vulnerabilities/fi/",
        parameter="page",
        severity="high",
        description="Local file inclusion vulnerability",
    ),
]


def validate_against_ground_truth(
    findings: list[Finding],
    ground_truth: list[GroundTruthVulnerability],
) -> dict:
    """
    Validate scan findings against known ground truth.

    Returns:
        Dict with TP, FP, FN counts and metrics
    """
    true_positives = []
    false_positives = []
    false_negatives = []
    matched_ground_truth = set()

    for finding in findings:
        matched = False
        for gt in ground_truth:
            if gt.matches_finding(finding):
                matched = True
                matched_ground_truth.add(gt.name)
                true_positives.append({
                    "finding": finding,
                    "ground_truth": gt,
                    "confidence": finding.confidence,
                })
                break

        if not matched:
            false_positives.append({
                "finding": finding,
                "reason": "No matching ground truth vulnerability",
            })

    # Find false negatives (ground truth not found)
    for gt in ground_truth:
        if gt.name not in matched_ground_truth:
            false_negatives.append({
                "ground_truth": gt,
                "reason": "Not detected by scanner",
            })

    tp = len(true_positives)
    fp = len(false_positives)
    fn = len(false_negatives)

    # Calculate metrics
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "metrics": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "recall": recall,
            "precision": precision,
            "f1_score": f1,
        },
        "coverage": {
            "total_ground_truth": len(ground_truth),
            "matched": len(matched_ground_truth),
            "coverage_percent": len(matched_ground_truth) / len(ground_truth) * 100 if ground_truth else 0,
        },
    }
