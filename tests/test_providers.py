import pytest

from tripweaver.core.config import Settings
from tripweaver.domain.schemas import ItineraryRequest
from tripweaver.providers.factory import build_llm_provider, build_search_provider
from tripweaver.providers.llm import MockLLMProvider
from tripweaver.providers.search import MockSearchProvider


@pytest.mark.asyncio
async def test_mock_search_provider():
    provider = MockSearchProvider()
    request = ItineraryRequest(
        destination="Chengdu",
        days=2,
        interests=["food", "pandas"],
    )

    results = await provider.search_places(request)

    assert len(results) == 3
    assert results[0].name == "Chengdu Museum"
    assert results[0].category == "museum"
    assert "Chengdu" in results[0].reason

    assert results[1].name == "Chengdu Old Town"
    assert results[1].category == "landmark"

    assert results[2].name == "Chengdu Food Street"
    assert results[2].category == "food"


@pytest.mark.asyncio
async def test_mock_llm_provider():
    provider = MockLLMProvider()
    request = ItineraryRequest(
        destination="Guangzhou",
        days=2,
        interests=["food", "culture"],
    )

    test_candidates = await MockSearchProvider().search_places(request)
    response = await provider.generate_itinerary(request, test_candidates)

    assert response.destination == "Guangzhou"
    assert "2-day trip in Guangzhou" in response.overview
    assert len(response.items) == 2

    assert response.items[0].day == 1
    assert "Day 1 in Guangzhou" in response.items[0].title
    assert len(response.items[0].places) == 3

    assert response.items[1].day == 2
    assert "Day 2 in Guangzhou" in response.items[1].title
    assert len(response.items[1].places) == 3

    # 验证三方案输出
    assert len(response.plan_options) == 3
    plan_names = [p["plan_name"] for p in response.plan_options]
    assert "休闲逛吃" in plan_names
    assert "景点打卡" in plan_names
    assert "小众特色" in plan_names
    for plan in response.plan_options:
        assert "plan_desc" in plan
        assert "destination" in plan
        assert "overview" in plan
        assert "items" in plan


def test_provider_factory():
    mock_settings = Settings(
        search_provider="mock",
        llm_provider="mock",
    )

    search_provider = build_search_provider(mock_settings)
    assert isinstance(search_provider, MockSearchProvider)

    llm_provider = build_llm_provider(mock_settings)
    assert isinstance(llm_provider, MockLLMProvider)

    with pytest.raises(ValueError, match="Unsupported search provider:invalid"):
        build_search_provider(Settings(search_provider="invalid"))

    with pytest.raises(ValueError, match="Unsupported llm provider:invalid"):
        build_llm_provider(Settings(llm_provider="invalid"))
