import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.comparison import ScanComparison
from app.models.result import Vulnerability
from app.models.scan import Scan
from app.schemas.comparison import ComparisonResponse
from app.schemas.result import VulnerabilityResponse


class ComparisonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compare(
        self, scan_a_id: uuid.UUID, scan_b_id: uuid.UUID, user_id: uuid.UUID
    ) -> ComparisonResponse:
        # Verify both scans belong to user
        for sid in (scan_a_id, scan_b_id):
            result = await self.db.execute(
                select(Scan).where(Scan.id == sid, Scan.user_id == user_id)
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError(f"Scan {sid} not found")

        # Get vulnerabilities for both scans
        vulns_a = await self._get_vulns(scan_a_id)
        vulns_b = await self._get_vulns(scan_b_id)

        # Build fingerprints for comparison
        fp_a = {self._fingerprint(v): v for v in vulns_a}
        fp_b = {self._fingerprint(v): v for v in vulns_b}

        keys_a = set(fp_a.keys())
        keys_b = set(fp_b.keys())

        new_keys = keys_b - keys_a
        fixed_keys = keys_a - keys_b
        unchanged_keys = keys_a & keys_b

        return ComparisonResponse(
            scan_a_id=scan_a_id,
            scan_b_id=scan_b_id,
            new_vulnerabilities=[
                VulnerabilityResponse.model_validate(fp_b[k]) for k in new_keys
            ],
            fixed_vulnerabilities=[
                VulnerabilityResponse.model_validate(fp_a[k]) for k in fixed_keys
            ],
            unchanged_vulnerabilities=[
                VulnerabilityResponse.model_validate(fp_b[k]) for k in unchanged_keys
            ],
            summary={
                "new": len(new_keys),
                "fixed": len(fixed_keys),
                "unchanged": len(unchanged_keys),
            },
        )

    async def _get_vulns(self, scan_id: uuid.UUID) -> list[Vulnerability]:
        result = await self.db.execute(
            select(Vulnerability).where(Vulnerability.scan_id == scan_id)
        )
        return list(result.scalars().all())

    @staticmethod
    def _fingerprint(vuln: Vulnerability) -> str:
        return f"{vuln.module_name}:{vuln.vuln_type}:{vuln.affected_url}:{vuln.affected_parameter or ''}"
