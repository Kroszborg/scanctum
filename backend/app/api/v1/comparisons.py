import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.comparison import ComparisonResponse
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/compare", tags=["comparisons"])


@router.get("/{scan_a_id}/{scan_b_id}", response_model=ComparisonResponse)
async def compare_scans(
    scan_a_id: uuid.UUID,
    scan_b_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ComparisonService(db)
    return await service.compare(scan_a_id, scan_b_id, current_user.id)
