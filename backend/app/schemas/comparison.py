import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.result import VulnerabilityResponse


class ComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_a_id: uuid.UUID
    scan_b_id: uuid.UUID
    new_vulnerabilities: list[VulnerabilityResponse] = []
    fixed_vulnerabilities: list[VulnerabilityResponse] = []
    unchanged_vulnerabilities: list[VulnerabilityResponse] = []
    summary: dict = {}
