import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.result import Vulnerability
from app.models.scan import Scan
from app.schemas.dashboard import DashboardStats, RecentScan, SeverityCount


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self, user_id: uuid.UUID) -> DashboardStats:
        # Total scans
        total_result = await self.db.execute(
            select(func.count(Scan.id)).where(Scan.user_id == user_id)
        )
        total_scans = total_result.scalar() or 0

        # Active scans
        active_result = await self.db.execute(
            select(func.count(Scan.id)).where(
                Scan.user_id == user_id,
                Scan.status.in_(["pending", "crawling", "scanning"]),
            )
        )
        active_scans = active_result.scalar() or 0

        # Total vulnerabilities
        vuln_result = await self.db.execute(
            select(func.count(Vulnerability.id))
            .join(Scan, Vulnerability.scan_id == Scan.id)
            .where(Scan.user_id == user_id)
        )
        total_vulns = vuln_result.scalar() or 0

        # Severity distribution
        severity_result = await self.db.execute(
            select(Vulnerability.severity, func.count(Vulnerability.id))
            .join(Scan, Vulnerability.scan_id == Scan.id)
            .where(Scan.user_id == user_id)
            .group_by(Vulnerability.severity)
        )
        severity_map = dict(severity_result.all())
        severity_dist = SeverityCount(
            critical=severity_map.get("critical", 0),
            high=severity_map.get("high", 0),
            medium=severity_map.get("medium", 0),
            low=severity_map.get("low", 0),
            info=severity_map.get("info", 0),
        )

        # Recent scans
        recent_result = await self.db.execute(
            select(Scan)
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(10)
        )
        recent_scans = []
        for scan in recent_result.scalars().all():
            vuln_count_r = await self.db.execute(
                select(func.count(Vulnerability.id)).where(Vulnerability.scan_id == scan.id)
            )
            recent_scans.append(
                RecentScan(
                    id=str(scan.id),
                    target_url=scan.target_url,
                    status=scan.status,
                    scan_mode=scan.scan_mode,
                    vuln_count=vuln_count_r.scalar() or 0,
                    created_at=scan.created_at.isoformat(),
                )
            )

        # Scans over time (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        time_result = await self.db.execute(
            select(
                func.date_trunc("day", Scan.created_at).label("day"),
                func.count(Scan.id),
            )
            .where(Scan.user_id == user_id, Scan.created_at >= thirty_days_ago)
            .group_by("day")
            .order_by("day")
        )
        scans_over_time = [
            {"date": row[0].isoformat(), "count": row[1]} for row in time_result.all()
        ]

        return DashboardStats(
            total_scans=total_scans,
            active_scans=active_scans,
            total_vulnerabilities=total_vulns,
            critical_count=severity_dist.critical,
            severity_distribution=severity_dist,
            recent_scans=recent_scans,
            scans_over_time=scans_over_time,
        )
