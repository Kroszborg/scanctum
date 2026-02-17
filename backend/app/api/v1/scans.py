import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_async_session
from app.models.user import User
from app.schemas.result import VulnerabilityResponse
from app.schemas.scan import ScanCreate, ScanResponse, ScanStatus
from app.services.scan_service import ScanService
from app.services.result_service import ResultService

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("", response_model=ScanResponse)
async def create_scan(
    body: ScanCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    return await service.create_and_dispatch(current_user.id, body)


@router.get("", response_model=list[ScanResponse])
async def list_scans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    return await service.list_scans(current_user.id, page, page_size, status)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    return await service.get_scan(scan_id, current_user.id)


@router.get("/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    return await service.get_scan_status(scan_id, current_user.id)


@router.get("/{scan_id}/results", response_model=list[VulnerabilityResponse])
async def get_scan_results(
    scan_id: uuid.UUID,
    severity: str | None = None,
    owasp: str | None = None,
    module: str | None = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ResultService(db)
    return await service.get_results(scan_id, current_user.id, severity, owasp, module)


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    await service.cancel_scan(scan_id, current_user.id)
    return {"detail": "Scan cancellation requested"}
