"""API endpoints for validation and testing."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from app.scanner.validation import (
    ScannerValidator,
    ValidationMetrics,
    print_validation_report,
    DVWA_GROUND_TRUTH,
    JUICE_SHOP_GROUND_TRUTH,
    WEBGOAT_GROUND_TRUTH,
)
from app.db.session import get_sync_session
from app.models.scan import Scan

router = APIRouter()


class ValidationRequest(BaseModel):
    target: str  # "dvwa", "juice_shop", "webgoat"
    target_url: str
    scan_mode: str = "full"


class ValidationResult(BaseModel):
    target: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    details: dict


class FindingsSummary(BaseModel):
    total_findings: int
    by_category: dict
    by_confidence: dict
    exploitable_count: int
    misconfiguration_count: int
    informational_count: int


@router.post("/api/v1/validate", response_model=ValidationResult)
async def run_validation(request: ValidationRequest):
    """
    Run validation scan against a test target (DVWA, Juice Shop, WebGoat).

    This automatically:
    1. Creates a scan against the target
    2. Waits for completion
    3. Validates findings against ground truth
    4. Returns precision/recall/F1 metrics
    """
    validator = ScannerValidator("http://localhost:8000")

    try:
        metrics = await validator.run_validation_scan(
            target_name=request.target,
            target_url=request.target_url,
            scan_mode=request.scan_mode,
        )

        return ValidationResult(
            target=request.target,
            true_positives=metrics.tp,
            false_positives=metrics.fp,
            false_negatives=metrics.fn,
            precision=metrics.precision,
            recall=metrics.recall,
            f1_score=metrics.f1_score,
            details=metrics.to_dict(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/validate/targets")
async def get_validation_targets():
    """Get available validation targets and their ground truth counts."""
    return {
        "dvwa": {
            "name": "DVWA",
            "description": "Damn Vulnerable Web Application (Low difficulty)",
            "ground_truth_count": len(DVWA_GROUND_TRUTH),
            "vulnerabilities": [
                {"name": gt.name, "type": gt.vuln_type, "location": gt.location}
                for gt in DVWA_GROUND_TRUTH
            ],
        },
        "juice_shop": {
            "name": "OWASP Juice Shop",
            "description": "OWASP Juice Shop v15.x",
            "ground_truth_count": len(JUICE_SHOP_GROUND_TRUTH),
            "vulnerabilities": [
                {"name": gt.name, "type": gt.vuln_type, "location": gt.location}
                for gt in JUICE_SHOP_GROUND_TRUTH
            ],
        },
        "webgoat": {
            "name": "WebGoat",
            "description": "OWASP WebGoat 2023.x",
            "ground_truth_count": len(WEBGOAT_GROUND_TRUTH),
            "vulnerabilities": [
                {"name": gt.name, "type": gt.vuln_type, "location": gt.location}
                for gt in WEBGOAT_GROUND_TRUTH
            ],
        },
    }


@router.get("/api/v1/scans/{scan_id}/findings/summary", response_model=FindingsSummary)
async def get_findings_summary(scan_id: str):
    """
    Get a summary of findings by category and confidence for a scan.

    Returns counts of exploitable vs misconfiguration vs informational findings.
    """
    from sqlalchemy import select
    from app.models.result import Vulnerability

    db = get_sync_session()

    try:
        # Fetch all vulnerabilities for this scan
        vulns = db.execute(
            select(Vulnerability).where(Vulnerability.scan_id == scan_id)
        ).scalars().all()

        by_category = {
            "exploitable": [],
            "misconfiguration": [],
            "informational": [],
        }
        by_confidence = {
            "confirmed": 0,
            "firm": 0,
            "tentative": 0,
            "low": 0,
        }

        for v in vulns:
            # Create temporary Finding object to get category
            from app.scanner.modules.base import Finding
            finding = Finding(
                module_name=v.module_name,
                vuln_type=v.vuln_type,
                severity=v.severity,
                cvss_score=v.cvss_score,
                cvss_vector=v.cvss_vector or "",
                owasp_category=v.owasp_category or "",
                cwe_id=v.cwe_id or "",
                affected_url=v.affected_url,
                affected_parameter=v.affected_parameter,
                description=v.description or "",
                remediation=v.remediation or "",
                confidence=v.confidence or "firm",
            )

            category = finding.get_category().value
            by_category[category].append({
                "id": v.id,
                "vuln_type": v.vuln_type,
                "severity": v.severity,
                "cvss_score": v.cvss_score,
                "affected_url": v.affected_url,
                "confidence": v.confidence,
            })

            if v.confidence in by_confidence:
                by_confidence[v.confidence] += 1

        return FindingsSummary(
            total_findings=len(vulns),
            by_category=by_category,
            by_confidence=by_confidence,
            exploitable_count=len(by_category["exploitable"]),
            misconfiguration_count=len(by_category["misconfiguration"]),
            informational_count=len(by_category["informational"]),
        )
    finally:
        db.close()


@router.post("/api/v1/verify")
async def verify_finding(
    url: str,
    payload: str,
    vuln_type: str,
    method: str = "GET",
    parameter: Optional[str] = None,
):
    """
    Manually verify a vulnerability finding.

    This endpoint:
    1. Sends the payload to the target URL
    2. Analyzes the response for confirmation
    3. Returns verification status with evidence
    """
    import httpx
    import re

    # SQLi verification patterns
    SQL_PATTERNS = [
        re.compile(r"you have an error in your sql syntax", re.I),
        re.compile(r"PostgreSQL.*ERROR", re.I),
        re.compile(r"ORA-\d{5}", re.I),
    ]

    # SSTI verification
    SSTI_RESULTS = ["49", "7777777", "30858025"]

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            if method == "GET":
                test_url = f"{url}?test={payload}" if "?" not in url else f"{url}&test={payload}"
                response = await client.get(test_url)
            else:
                response = await client.post(url, data={"test": payload})

            verified = False
            confidence = "low"
            evidence = {}
            explanation = "No vulnerability detected"

            # Check for SQLi
            if "sql" in vuln_type.lower():
                for pattern in SQL_PATTERNS:
                    if pattern.search(response.text):
                        verified = True
                        confidence = "confirmed"
                        evidence = {"sql_error_found": True}
                        explanation = "SQL error message confirms injection"
                        break

            # Check for SSTI
            elif "ssti" in vuln_type.lower() or "template" in vuln_type.lower():
                for result in SSTI_RESULTS:
                    if result in response.text and payload not in response.text:
                        verified = True
                        confidence = "confirmed"
                        evidence = {"ssti_result_found": result}
                        explanation = f"Template evaluation confirmed (found '{result}')"
                        break

            # Check for XSS
            elif "xss" in vuln_type.lower():
                if payload in response.text:
                    verified = True
                    confidence = "firm"
                    evidence = {"payload_reflected": True}
                    explanation = "Payload reflected in response"

            return {
                "verified": verified,
                "confidence": confidence,
                "evidence": evidence,
                "explanation": explanation,
                "response_status": response.status_code,
                "response_length": len(response.text),
            }

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Request failed: {str(e)}")


@router.get("/api/v1/zap-comparison/status")
async def get_zap_status():
    """Check if ZAP CLI is installed and available."""
    import subprocess

    try:
        result = subprocess.run(["zap-cli", "--version"], capture_output=True, text=True)
        return {"installed": True, "version": result.stdout.strip()}
    except FileNotFoundError:
        return {"installed": False, "message": "ZAP CLI not installed. Run: pip install zap-cli"}
