import uuid

from pydantic import BaseModel, ConfigDict


class ReportRequest(BaseModel):
    format: str = "pdf"


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: uuid.UUID
    format: str
    filename: str
    content_type: str
