"""Target asset inventory endpoint — aggregates scan data by target URL."""
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.result import Vulnerability
from app.models.scan import Scan
from app.models.user import User

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetSummary(BaseModel):
    """Aggregated stats for a single scanned target URL."""
    model_config = ConfigDict(from_attributes=True)

    target_url: str
    scan_count: int
    last_scan_id: str
    last_scan_status: str
    last_scan_at: datetime | None
    total_vulns: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    last_scan_mode: str


@router.get("", response_model=list[AssetSummary])
async def list_assets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AssetSummary]:
    """Return one entry per unique target URL the user has scanned.

    Each entry aggregates: scan count, latest scan status, vulnerability counts
    per severity, and most recent scan metadata.
    """
    # Get all completed scans for the user
    scans_stmt = (
        select(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
    )
    result = await db.execute(scans_stmt)
    all_scans = result.scalars().all()

    # Group by target_url
    groups: dict[str, list[Scan]] = {}
    for scan in all_scans:
        groups.setdefault(scan.target_url, []).append(scan)

    assets: list[AssetSummary] = []
    for target_url, scans in groups.items():
        latest = scans[0]  # Already ordered by created_at desc

        # Count vulnerabilities across ALL scans for this target
        scan_ids = [s.id for s in scans]

        vuln_counts: dict[str, int] = {}
        for sev in ("critical", "high", "medium", "low", "info"):
            count_stmt = select(func.count(Vulnerability.id)).where(
                and_(
                    Vulnerability.scan_id.in_(scan_ids),
                    Vulnerability.severity == sev,
                    Vulnerability.is_false_positive == False,
                )
            )
            r = await db.execute(count_stmt)
            vuln_counts[sev] = r.scalar_one()

        total_stmt = select(func.count(Vulnerability.id)).where(
            and_(
                Vulnerability.scan_id.in_(scan_ids),
                Vulnerability.is_false_positive == False,
            )
        )
        tr = await db.execute(total_stmt)
        total_vulns = tr.scalar_one()

        assets.append(AssetSummary(
            target_url=target_url,
            scan_count=len(scans),
            last_scan_id=str(latest.id),
            last_scan_status=latest.status,
            last_scan_at=latest.completed_at or latest.started_at or latest.created_at,
            total_vulns=total_vulns,
            critical_count=vuln_counts["critical"],
            high_count=vuln_counts["high"],
            medium_count=vuln_counts["medium"],
            low_count=vuln_counts["low"],
            info_count=vuln_counts["info"],
            last_scan_mode=latest.scan_mode,
        ))

    # Sort by risk: critical first, then high, then total
    assets.sort(key=lambda a: (-a.critical_count, -a.high_count, -a.total_vulns))
    return assets
