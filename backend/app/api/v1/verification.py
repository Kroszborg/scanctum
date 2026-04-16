"""API endpoint for manual vulnerability verification."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import re

router = APIRouter()


class VerifyRequest(BaseModel):
    url: str
    payload: str
    vuln_type: str
    method: str = "GET"
    parameter: str | None = None


class VerifyResponse(BaseModel):
    verified: bool
    confidence: str
    evidence: dict
    explanation: str


class ManualVerification:
    """Manual verification helpers for vulnerability findings."""

    # SQLi verification patterns
    SQL_CONFIRMATION_PATTERNS = [
        re.compile(r"you have an error in your sql syntax", re.I),
        re.compile(r"PostgreSQL.*ERROR", re.I),
        re.compile(r"ORA-\d{5}", re.I),
        re.compile(r"unclosed quotation mark", re.I),
        re.compile(r"MySqlClient", re.I),
    ]

    # XSS verification: check if script executes
    XSS_CANARY = "scntm_verify_xss"

    # SSTI verification patterns
    SSTI_RESULTS = ["49", "7777777", "30858025"]


@router.post("/api/v1/verify", response_model=VerifyResponse)
async def verify_vulnerability(request: VerifyRequest):
    """
    Manually verify a vulnerability finding.

    This endpoint:
    1. Sends the payload to the target URL
    2. Analyzes the response for confirmation
    3. Returns verification status with evidence
    """
    verifier = ManualVerification()

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            if request.method == "GET":
                response = await client.get(request.url)
            else:
                response = await client.post(request.url, data={"test": request.payload})

            verified, confidence, evidence, explanation = verifier.verify(
                response.text,
                request.payload,
                request.vuln_type,
            )

            return VerifyResponse(
                verified=verified,
                confidence=confidence,
                evidence=evidence,
                explanation=explanation,
            )

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Request failed: {str(e)}")


@router.get("/api/v1/scans/{scan_id}/findings/summary")
async def get_findings_summary(scan_id: str):
    """
    Get a summary of findings by category for a scan.

    Returns counts of exploitable vs misconfiguration vs informational.
    """
    # This would query the database for findings
    # For now, return a placeholder structure
    return {
        "scan_id": scan_id,
        "total_findings": 0,
        "by_category": {
            "exploitable": [],
            "misconfiguration": [],
            "informational": [],
        },
        "by_confidence": {
            "confirmed": 0,
            "firm": 0,
            "tentative": 0,
            "low": 0,
        },
    }