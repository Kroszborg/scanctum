import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_create_scan(client: AsyncClient, auth_headers: dict):
    with patch("app.services.scan_service.run_scan") as mock_task:
        mock_task.delay.return_value = MagicMock(id="fake-task-id")
        response = await client.post(
            "/api/v1/scans",
            json={"target_url": "https://example.com", "scan_mode": "quick"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["target_url"] == "https://example.com/"
    assert data["scan_mode"] == "quick"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_scans_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/scans", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_scans_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/scans")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_scan_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/v1/scans/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404
