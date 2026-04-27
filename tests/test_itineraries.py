import pytest
from fastapi.testclient import TestClient

from tripweaver.core.config import get_settings
from tripweaver.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def use_mock_providers(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()


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
