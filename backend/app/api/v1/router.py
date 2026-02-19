from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.scans import router as scans_router
from app.api.v1.reports import router as reports_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.comparisons import router as comparisons_router
from app.api.v1.ws import router as ws_router
from app.api.v1.vulnerabilities import router as vulns_router
from app.api.v1.assets import router as assets_router
from app.api.v1.schedules import router as schedules_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(scans_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
api_router.include_router(comparisons_router)
api_router.include_router(ws_router)
api_router.include_router(vulns_router)
api_router.include_router(assets_router)
api_router.include_router(schedules_router)
