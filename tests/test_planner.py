import pytest
from unittest.mock import AsyncMock

from tripweaver.domain.schemas import (
    CandidatePlace,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
)
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


class TestMatchCandidate:
    """测试候选POI名称匹配"""

    def test_exact_match(self):
        """精确匹配：名称完全一致"""
        cmap = {"库迪咖啡": (121.0, 31.0)}
        result = PlannerService._match_candidate("库迪咖啡", cmap)
        assert result == (121.0, 31.0)

    def test_fuzzy_match_candidate_in_name(self):
        """模糊匹配：候选名包含在LLM地名中"""
        cmap = {"新世界大丸百货": (121.0, 31.0)}
        result = PlannerService._match_candidate("新世界大丸百货B2美食层", cmap)
        assert result == (121.0, 31.0)

    def test_fuzzy_match_name_in_candidate(self):
        """模糊匹配：LLM地名包含在候选名中"""
        cmap = {"新世界大丸百货B2美食层": (121.0, 31.0)}
        result = PlannerService._match_candidate("新世界大丸百货", cmap)
        assert result == (121.0, 31.0)

    def test_no_match(self):
        """无匹配"""
        cmap = {"库迪咖啡": (121.0, 31.0)}
        result = PlannerService._match_candidate("完全未知的地点", cmap)
        assert result is None


@pytest.mark.asyncio
async def test_backfill_coordinates():
    """测试坐标回填：精确匹配 + 模糊匹配 + 地理编码"""
    candidates = [
        CandidatePlace(
            name="库迪咖啡(南京东路地铁站店)",
            category="饮品",
            reason="测试",
            address="南京东路地铁站内",
            longitude=121.4805,
            latitude=31.2365,
        ),
        CandidatePlace(
            name="新世界大丸百货",
            category="购物",
            reason="测试",
            address="南京东路228号",
            longitude=121.4798,
            latitude=31.2370,
        ),
    ]
    response = ItineraryResponse(
        destination="南京东路",
        overview="测试",
        items=[
            ItineraryItem(
                day=1,
                title="Day 1",
                summary="测试",
                places=[
                    CandidatePlace(
                        name="库迪咖啡(南京东路地铁站店)",  # 精确匹配
                        category="饮品", reason="推荐", address="南京东路地铁站内",
                        longitude=None, latitude=None,
                    ),
                    CandidatePlace(
                        name="新世界大丸百货B2美食层",  # 模糊匹配
                        category="美食", reason="推荐", address="南京东路228号B2",
                        longitude=None, latitude=None,
                    ),
                    CandidatePlace(
                        name="完全未知的地点",  # 需要地理编码
                        category="景点", reason="推荐", address="上海市黄浦区某路123号",
                        longitude=None, latitude=None,
                    ),
                ],
            )
        ],
        plan_options=[],
    )

    mock_amap = AsyncMock()
    mock_amap.geocode_address = AsyncMock(return_value=(121.5000, 31.2000))

    planner = PlannerService(
        search_provider=AsyncMock(),
        llm_provider=AsyncMock(),
        amap_provider=mock_amap,
    )

    await planner._backfill_coordinates(response, candidates)

    places = response.items[0].places
    # 精确匹配
    assert places[0].longitude == 121.4805
    assert places[0].latitude == 31.2365
    # 模糊匹配
    assert places[1].longitude == 121.4798
    assert places[1].latitude == 31.2370
    # 地理编码
    assert places[2].longitude == 121.5000
    assert places[2].latitude == 31.2000


@pytest.mark.asyncio
async def test_backfill_plan_options_dicts():
    """测试 plan_options 中的 dict 也会被回填坐标（与 response.items 同时设置）"""
    candidates = [
        CandidatePlace(
            name="测试咖啡",
            category="饮品", reason="测试",
            longitude=121.48, latitude=31.23,
        ),
    ]
    # plan_options 中的 places 是 dict（模拟 LLM 返回后的真实结构）
    response = ItineraryResponse(
        destination="测试", overview="测试",
        items=[
            ItineraryItem(
                day=1, title="Day 1", summary="测试",
                places=[
                    CandidatePlace(
                        name="测试咖啡", category="饮品", reason="推荐",
                        longitude=None, latitude=None,
                    ),
                ],
            )
        ],
        plan_options=[
            {
                "title": "方案1",
                "description": "测试",
                "overview": "测试",
                "items": [
                    {
                        "day": 1, "title": "Day 1", "summary": "测试",
                        "places": [
                            {
                                "name": "测试咖啡",
                                "category": "饮品",
                                "reason": "推荐",
                                "address": "测试地址",
                                "longitude": None,
                                "latitude": None,
                            }
                        ],
                    }
                ],
            }
        ],
    )

    planner = PlannerService(
        search_provider=AsyncMock(),
        llm_provider=AsyncMock(),
        amap_provider=None,
    )

    await planner._backfill_coordinates(response, candidates)

    # response.items 中的 CandidatePlace 对象
    assert response.items[0].places[0].longitude == 121.48
    assert response.items[0].places[0].latitude == 31.23
    # plan_options 中的 dict 也要有坐标
    plan_place = response.plan_options[0]["items"][0]["places"][0]
    assert plan_place["longitude"] == 121.48
    assert plan_place["latitude"] == 31.23


@pytest.mark.asyncio
async def test_backfill_no_amap_provider():
    """无 amap provider 时只做名称匹配，不调用地理编码"""
    candidates = [
        CandidatePlace(
            name="测试地点",
            category="景点", reason="测试",
            longitude=121.0, latitude=31.0,
        ),
    ]
    response = ItineraryResponse(
        destination="测试", overview="测试",
        items=[
            ItineraryItem(
                day=1, title="Day 1", summary="测试",
                places=[
                    CandidatePlace(
                        name="测试地点", category="景点", reason="测试",
                        longitude=None, latitude=None,
                    ),
                    CandidatePlace(
                        name="未知地点", category="景点", reason="测试",
                        address="某地址", longitude=None, latitude=None,
                    ),
                ],
            )
        ],
    )

    planner = PlannerService(
        search_provider=AsyncMock(),
        llm_provider=AsyncMock(),
        amap_provider=None,
    )

    await planner._backfill_coordinates(response, candidates)

    places = response.items[0].places
    assert places[0].longitude == 121.0
    # 无 amap provider，无法地理编码
    assert places[1].longitude is None


@pytest.mark.asyncio
async def test_backfill_skips_already_has_coords():
    """已有坐标的地点不参与回填"""
    candidates = [
        CandidatePlace(
            name="测试地点", category="景点", reason="测试",
            longitude=121.0, latitude=31.0,
        ),
    ]
    response = ItineraryResponse(
        destination="测试", overview="测试",
        items=[
            ItineraryItem(
                day=1, title="Day 1", summary="测试",
                places=[
                    CandidatePlace(
                        name="测试地点", category="景点", reason="测试",
                        longitude=122.0, latitude=32.0,  # 已有坐标
                    ),
                ],
            )
        ],
    )

    planner = PlannerService(
        search_provider=AsyncMock(),
        llm_provider=AsyncMock(),
        amap_provider=AsyncMock(),
    )

    await planner._backfill_coordinates(response, candidates)

    # 坐标不变（不会被覆盖）
    assert response.items[0].places[0].longitude == 122.0
    assert response.items[0].places[0].latitude == 32.0
