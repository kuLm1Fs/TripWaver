from fastapi.testclient import TestClient
from tripweaver.main import app

client = TestClient(app)


def test_plan_itinerary() -> None:
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
