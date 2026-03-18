import uuid
from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import func, select, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cached, hot_cache, invalidate_pattern
from app.models.result import Vulnerability
from app.models.scan import Scan
from app.schemas.dashboard import DashboardStats, RecentScan, SeverityCount


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @cached(key_prefix="dashboard:stats", ttl=60, key_fn=lambda self, user_id: str(user_id))
    async def get_stats(self, user_id: uuid.UUID) -> DashboardStats:
        """
        Get dashboard statistics with caching.
        Cache TTL: 60 seconds (balances freshness vs. database load).
        Uses single optimized query instead of N+1 queries.
        """
        # Check in-memory hot cache first
        cached_stats = await hot_cache.get(f"dashboard:stats:{user_id}")
        if cached_stats:
            return DashboardStats(**cached_stats)

        # Optimized single-query approach with subquery for vulnerability counts
        vuln_counts_subq = (
            select(
                Vulnerability.scan_id,
                func.count(Vulnerability.id).label("total_vulns"),
                func.count(case((Vulnerability.severity == "critical", 1), else_=None)).label("critical_count"),
                func.count(case((Vulnerability.severity == "high", 1), else_=None)).label("high_count"),
                func.count(case((Vulnerability.severity == "medium", 1), else_=None)).label("medium_count"),
                func.count(case((Vulnerability.severity == "low", 1), else_=None)).label("low_count"),
                func.count(case((Vulnerability.severity == "info", 1), else_=None)).label("info_count"),
            )
            .group_by(Vulnerability.scan_id)
            .subquery()
        )

        # Main query with LEFT JOIN to include scans without vulnerabilities
        scans_result = await self.db.execute(
            select(
                Scan.id,
                Scan.target_url,
                Scan.status,
                Scan.scan_mode,
                Scan.created_at,
                func.coalesce(vuln_counts_subq.c.total_vulns, 0).label("vuln_count"),
                func.coalesce(vuln_counts_subq.c.critical_count, 0).label("critical_count"),
                func.coalesce(vuln_counts_subq.c.high_count, 0).label("high_count"),
                func.coalesce(vuln_counts_subq.c.medium_count, 0).label("medium_count"),
                func.coalesce(vuln_counts_subq.c.low_count, 0).label("low_count"),
                func.coalesce(vuln_counts_subq.c.info_count, 0).label("info_count"),
            )
            .outerjoin(vuln_counts_subq, Scan.id == vuln_counts_subq.c.scan_id)
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(10)
        )

        scan_rows = scans_result.all()

        # Build recent scans list
        # row indices: 0=id, 1=target_url, 2=status, 3=scan_mode, 4=created_at,
        #              5=vuln_count, 6=critical_count, 7=high_count, 8=medium_count,
        #              9=low_count, 10=info_count
        recent_scans = [
            RecentScan(
                id=str(row[0]),
                target_url=row[1],
                status=row[2],
                scan_mode=row[3],
                vuln_count=int(row[5]),
                created_at=row[4].isoformat(),
            )
            for row in scan_rows
        ]

        # Aggregate severity from recent scans (approximation for full dataset)
        total_critical = sum(int(row[6]) for row in scan_rows)
        total_high = sum(int(row[7]) for row in scan_rows)
        total_medium = sum(int(row[8]) for row in scan_rows)
        total_low = sum(int(row[9]) for row in scan_rows)
        total_info = sum(int(row[10]) for row in scan_rows)

        # Separate queries for totals (cannot be fully optimized into single query)
        # These are cached so impact is minimized
        total_scans_result = await self.db.execute(
            select(func.count(Scan.id)).where(Scan.user_id == user_id)
        )
        total_scans = total_scans_result.scalar() or 0

        active_scans_result = await self.db.execute(
            select(func.count(Scan.id)).where(
                Scan.user_id == user_id,
                Scan.status.in_(["pending", "crawling", "scanning"]),
            )
        )
        active_scans = active_scans_result.scalar() or 0

        # Severity distribution (full dataset, not just recent scans)
        severity_result = await self.db.execute(
            select(
                Vulnerability.severity,
                func.count(Vulnerability.id).label("count"),
            )
            .join(Scan, Vulnerability.scan_id == Scan.id)
            .where(Scan.user_id == user_id)
            .group_by(Vulnerability.severity)
        )
        severity_map = {row[0]: row[1] for row in severity_result.all()}
        severity_dist = SeverityCount(
            critical=severity_map.get("critical", 0),
            high=severity_map.get("high", 0),
            medium=severity_map.get("medium", 0),
            low=severity_map.get("low", 0),
            info=severity_map.get("info", 0),
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

        stats = DashboardStats(
            total_scans=total_scans,
            active_scans=active_scans,
            total_vulnerabilities=severity_dist.critical + severity_dist.high + severity_dist.medium + severity_dist.low + severity_dist.info,
            critical_count=severity_dist.critical,
            severity_distribution=severity_dist,
            recent_scans=recent_scans,
            scans_over_time=scans_over_time,
        )

        # Store in hot cache (in-memory, fast access)
        await hot_cache.set(
            f"dashboard:stats:{user_id}",
            {
                "total_scans": stats.total_scans,
                "active_scans": stats.active_scans,
                "total_vulnerabilities": stats.total_vulnerabilities,
                "critical_count": stats.critical_count,
                "severity_distribution": {
                    "critical": stats.severity_distribution.critical,
                    "high": stats.severity_distribution.high,
                    "medium": stats.severity_distribution.medium,
                    "low": stats.severity_distribution.low,
                    "info": stats.severity_distribution.info,
                },
                "recent_scans": [
                    {
                        "id": s.id,
                        "target_url": s.target_url,
                        "status": s.status,
                        "scan_mode": s.scan_mode,
                        "vuln_count": s.vuln_count,
                        "created_at": s.created_at,
                    }
                    for s in stats.recent_scans
                ],
                "scans_over_time": stats.scans_over_time,
            },
        )

        return stats

    async def invalidate_cache(self, user_id: uuid.UUID) -> None:
        """Invalidate dashboard cache when scan state changes."""
        await hot_cache.delete(f"dashboard:stats:{user_id}")
        await invalidate_pattern(f"dashboard:stats:{user_id}")
