import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class ScanCreate(BaseModel):
    target_url: HttpUrl
    scan_mode: str = "quick"
    config: dict | None = None


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    target_url: str
    scan_mode: str
    status: str
    progress_percent: int
    pages_found: int
    pages_scanned: int
    celery_task_id: str | None
    config: dict | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ScanStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    progress_percent: int
    pages_found: int
    pages_scanned: int
    error_message: str | None
