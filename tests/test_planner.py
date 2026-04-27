import pytest

from tripweaver.domain.schemas import ItineraryRequest
from tripweaver.providers.llm import MockLLMProvider
from tripweaver.providers.search import MockSearchProvider
from tripweaver.services.planner import PlannerService


@pytest.fixture
def planner_service():
    return PlannerService(
        search_provider=MockSearchProvider(),
        llm_provider=MockLLMProvider(),
    )


@pytest.mark.asyncio
async def test_planner_plan_success(planner_service):
    request = ItineraryRequest(
        destination="Beijing",
        days=3,
        interests=["history", "food"],
    )

    response = await planner_service.plan(request)

    assert response.destination == "Beijing"
    assert len(response.items) == 3
    assert "Beijing" in response.overview

    for day in range(1, 4):
        item = response.items[day - 1]
        assert item.day == day
        assert f"Day {day}" in item.title
        assert len(item.places) == 3
        assert any("Museum" in p.name for p in item.places)
        assert any("Old Town" in p.name for p in item.places)
        assert any("Food Street" in p.name for p in item.places)
