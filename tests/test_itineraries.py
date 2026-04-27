from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from tripweaver.core.config import get_settings
from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user_id
from tripweaver.main import app

client = TestClient(app)


class FakeSession:
    """模拟数据库会话，add时自动填充id"""

    def __init__(self):
        self._counter = 0

    def add(self, obj):
        self._counter += 1
        obj.id = self._counter

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


@pytest.fixture(autouse=True)
def use_mock_providers(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def mock_auth():
    """绕过JWT认证，直接返回测试用户ID"""
    app.dependency_overrides[get_current_user_id] = lambda: 1
    yield
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture(autouse=True)
def mock_db():
    """模拟数据库会话"""
    app.dependency_overrides[get_db] = lambda: FakeSession()
    yield
    app.dependency_overrides.pop(get_db, None)


def test_plan_itinerary_success() -> None:
    response = client.post(
        "/api/v1/itineraries/plan",
        json={
            "destination": "Shanghai",
            "days": 2,
            "interests": ["food", "museum"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Shanghai"
    assert len(data["items"]) == 2
    assert "overview" in data
    for item in data["items"]:
        assert "day" in item
        assert "title" in item
        assert "summary" in item
        assert len(item["places"]) == 3


def test_plan_itinerary_invalid_request() -> None:
    response = client.post(
        "/api/v1/itineraries/plan",
        json={
            "days": 2,
            "interests": ["food", "museum"],
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/itineraries/plan",
        json={
            "destination": "Shanghai",
            "days": 0,
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/api/v1/itineraries/plan",
        json={
            "destination": "Shanghai",
            "days": 31,
        },
    )
    assert response.status_code == 422
