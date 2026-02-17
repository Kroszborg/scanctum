import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evidence_type: str
    title: str
    content: str
    order_index: int


class VulnerabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_id: uuid.UUID
    module_name: str
    vuln_type: str
    severity: str
    cvss_score: float
    cvss_vector: str
    owasp_category: str
    cwe_id: str
    affected_url: str
    affected_parameter: str | None
    description: str
    remediation: str
    confidence: str
    is_false_positive: bool
    created_at: datetime
    evidence: list[EvidenceResponse] = []
