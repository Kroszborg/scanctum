import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_async_session
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{scan_id}")
async def get_report(
    scan_id: uuid.UUID,
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)

    if format == "json":
        data = await service.generate_json_report(scan_id, current_user.id)
        return JSONResponse(content=data)

    pdf_bytes = await service.generate_pdf_report(scan_id, current_user.id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="scanctum-report-{scan_id}.pdf"'},
    )
