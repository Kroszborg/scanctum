"""Global vulnerability database endpoint — aggregates all vulns across user's scans."""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.result import Vulnerability
from app.models.scan import Scan
from app.models.user import User
from app.schemas.result import VulnerabilityResponse

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=list[VulnerabilityResponse])
async def list_all_vulnerabilities(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    severity: str | None = Query(None, description="Filter by severity (critical/high/medium/low/info)"),
    owasp: str | None = Query(None, description="Filter by OWASP category (e.g. A03)"),
    module: str | None = Query(None, description="Filter by module name"),
    confidence: str | None = Query(None, description="Filter by confidence (confirmed/firm/tentative)"),
    is_false_positive: bool | None = Query(None, description="Filter false positives"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[VulnerabilityResponse]:
    """Return all vulnerabilities across all of the current user's scans.

    Results are ordered by severity (critical first) then by creation date (newest first).
    """
    # Build severity ordering expression
    severity_order = {
        "critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4,
    }

    # Subquery: scan IDs belonging to current user
    user_scan_ids_stmt = select(Scan.id).where(Scan.user_id == current_user.id)

    stmt = select(Vulnerability).where(Vulnerability.scan_id.in_(user_scan_ids_stmt))

    if severity:
        stmt = stmt.where(Vulnerability.severity == severity.lower())
    if owasp:
        stmt = stmt.where(Vulnerability.owasp_category == owasp.upper())
    if module:
        stmt = stmt.where(Vulnerability.module_name == module.lower())
    if confidence:
        stmt = stmt.where(Vulnerability.confidence == confidence.lower())
    if is_false_positive is not None:
        stmt = stmt.where(Vulnerability.is_false_positive == is_false_positive)

    stmt = (
        stmt
        .order_by(Vulnerability.cvss_score.desc(), Vulnerability.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    vulns = result.scalars().all()
    return [VulnerabilityResponse.model_validate(v) for v in vulns]
