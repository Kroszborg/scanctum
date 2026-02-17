from pydantic import BaseModel, ConfigDict


class SeverityCount(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class RecentScan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target_url: str
    status: str
    scan_mode: str
    vuln_count: int = 0
    created_at: str


class DashboardStats(BaseModel):
    total_scans: int = 0
    active_scans: int = 0
    total_vulnerabilities: int = 0
    critical_count: int = 0
    severity_distribution: SeverityCount = SeverityCount()
    recent_scans: list[RecentScan] = []
    scans_over_time: list[dict] = []
