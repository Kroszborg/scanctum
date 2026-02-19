"""Scheduled scans CRUD endpoint."""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/schedules", tags=["schedules"])

# ── In-memory store (no DB migration required for MVP) ─────────────────────
# In production, add a SQLAlchemy model and Alembic migration.
_store: dict[str, dict] = {}


class ScheduleCreate(BaseModel):
    target_url: str
    scan_mode: str = "quick"
    cron_expression: str  # e.g. "0 2 * * *" (daily at 02:00 UTC)
    label: str | None = None
    is_active: bool = True

    @field_validator("scan_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in ("quick", "full"):
            raise ValueError("scan_mode must be 'quick' or 'full'")
        return v

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("cron_expression must have exactly 5 fields (min hour dom mon dow)")
        return v.strip()


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    target_url: str
    scan_mode: str
    cron_expression: str
    label: str | None
    is_active: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime


class SchedulePatch(BaseModel):
    is_active: bool | None = None
    cron_expression: str | None = None
    label: str | None = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        if v is None:
            return v
        parts = v.strip().split()
        if len(parts) != 5:
            raise ValueError("cron_expression must have exactly 5 fields")
        return v.strip()


def _owned(record: dict, user: User) -> bool:
    return record["user_id"] == str(user.id)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ScheduleResponse]:
    records = [r for r in _store.values() if _owned(r, current_user)]
    records.sort(key=lambda r: r["created_at"], reverse=True)
    return [ScheduleResponse(**r) for r in records]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScheduleResponse:
    record = {
        "id": str(uuid.uuid4()),
        "user_id": str(current_user.id),
        "target_url": body.target_url,
        "scan_mode": body.scan_mode,
        "cron_expression": body.cron_expression,
        "label": body.label,
        "is_active": body.is_active,
        "last_run_at": None,
        "next_run_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    _store[record["id"]] = record
    return ScheduleResponse(**record)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScheduleResponse:
    record = _store.get(schedule_id)
    if not record or not _owned(record, current_user):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return ScheduleResponse(**record)


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    body: SchedulePatch,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScheduleResponse:
    record = _store.get(schedule_id)
    if not record or not _owned(record, current_user):
        raise HTTPException(status_code=404, detail="Schedule not found")
    if body.is_active is not None:
        record["is_active"] = body.is_active
    if body.cron_expression is not None:
        record["cron_expression"] = body.cron_expression
    if body.label is not None:
        record["label"] = body.label
    return ScheduleResponse(**record)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    record = _store.get(schedule_id)
    if not record or not _owned(record, current_user):
        raise HTTPException(status_code=404, detail="Schedule not found")
    del _store[schedule_id]
