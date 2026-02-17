import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.result import Vulnerability
from app.models.scan import Scan


class ResultService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_results(
        self,
        scan_id: uuid.UUID,
        user_id: uuid.UUID,
        severity: str | None = None,
        owasp: str | None = None,
        module: str | None = None,
    ) -> list[Vulnerability]:
        # Verify scan belongs to user
        result = await self.db.execute(
            select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Scan not found")

        query = select(Vulnerability).where(Vulnerability.scan_id == scan_id)

        if severity:
            query = query.where(Vulnerability.severity == severity)
        if owasp:
            query = query.where(Vulnerability.owasp_category == owasp)
        if module:
            query = query.where(Vulnerability.module_name == module)

        query = query.order_by(Vulnerability.cvss_score.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
