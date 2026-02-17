import uuid

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.scan import Scan
from app.schemas.scan import ScanCreate


class ScanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_dispatch(self, user_id: uuid.UUID, data: ScanCreate) -> Scan:
        scan = Scan(
            user_id=user_id,
            target_url=str(data.target_url),
            scan_mode=data.scan_mode,
            status="pending",
            config=data.config or {},
        )
        self.db.add(scan)
        await self.db.flush()
        await self.db.refresh(scan)

        # Dispatch Celery task
        from app.tasks.scan_tasks import run_scan
        task = run_scan.delay(str(scan.id))
        scan.celery_task_id = task.id
        await self.db.flush()
        await self.db.refresh(scan)

        return scan

    async def list_scans(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> list[Scan]:
        query = select(Scan).where(Scan.user_id == user_id).order_by(desc(Scan.created_at))
        if status:
            query = query.where(Scan.status == status)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_scan(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> Scan:
        result = await self.db.execute(
            select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
        )
        scan = result.scalar_one_or_none()
        if scan is None:
            raise NotFoundError("Scan not found")
        return scan

    async def get_scan_status(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> Scan:
        return await self.get_scan(scan_id, user_id)

    async def cancel_scan(self, scan_id: uuid.UUID, user_id: uuid.UUID) -> None:
        scan = await self.get_scan(scan_id, user_id)
        if scan.status in ("completed", "failed", "cancelled"):
            raise BadRequestError("Scan is not running")

        scan.status = "cancelled"
        await self.db.flush()

        if scan.celery_task_id:
            from app.tasks.celery_app import celery_app
            celery_app.control.revoke(scan.celery_task_id, terminate=True)
