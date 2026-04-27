from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.llm_prompt import (
    PLAN_STYLES,
    build_itinerary_prompt,
    build_single_plan_prompt,
)


def test_build_prompt_with_candidates():
    request = ItineraryRequest(
        destination="Xiamen",
        days=3,
        interests=["beach", "seafood"],
    )

    candidates = [
        CandidatePlace(
            name="Gulangyu Island",
            category="landmark",
            reason="Famous island with beaches and colonial architecture",
        ),
        CandidatePlace(
            name="Zeng Cuo An",
            category="food",
            reason="Seafood street with local snacks",
        ),
    ]

    prompt = build_itinerary_prompt(request, candidates)

    assert "Xiamen" in prompt
    assert "3 天" in prompt
    assert "beach, seafood" in prompt
    assert "Gulangyu Island" in prompt
    assert "Zeng Cuo An" in prompt
    assert "休闲逛吃" in prompt
    assert "景点打卡" in prompt
    assert "小众特色" in prompt
    assert "只能返回合法JSON" in prompt
    assert '"title"' in prompt
    assert '"destination": "Xiamen"' in prompt


def test_build_prompt_without_candidates():
    request = ItineraryRequest(
        destination="Lhasa",
        days=2,
        interests=[],
    )

    prompt = build_itinerary_prompt(request, [])

    assert "Lhasa" in prompt
    assert "2 天" in prompt
    assert "常规观光" in prompt
    assert "未找到候选地点。" in prompt
    assert "休闲逛吃" in prompt


def test_build_prompt_places_fields():
    """验证prompt包含新增的地点字段"""
    request = ItineraryRequest(destination="Chengdu", days=1)
    prompt = build_itinerary_prompt(request, [])

    assert "address" in prompt
    assert "longitude" in prompt
    assert "latitude" in prompt
    assert "price" in prompt
    assert "business_hours" in prompt
    assert "tags" in prompt


def test_plan_styles_count():
    """验证定义了 3 种方案风格"""
    assert len(PLAN_STYLES) == 3
    titles = [s["title"] for s in PLAN_STYLES]
    assert "休闲逛吃" in titles
    assert "景点打卡" in titles
    assert "小众特色" in titles


def test_build_single_plan_prompt():
    """验证单方案 prompt 包含正确的风格和目的地"""
    request = ItineraryRequest(
        destination="上海南京东路",
        days=1,
        interests=["二次元"],
    )
    candidates = [
        CandidatePlace(
            name="百联ZX创趣场",
            category="购物",
            reason="二次元圣地",
        ),
    ]
    style = PLAN_STYLES[1]  # 景点打卡

    prompt = build_single_plan_prompt(request, candidates, style)

    assert "上海南京东路" in prompt
    assert "景点打卡" in prompt
    assert "1 天" in prompt
    assert "百联ZX创趣场" in prompt
    assert "二次元" in prompt
    # 确保只返回单个对象，不是数组
    assert "单个对象，不是数组" in prompt
    assert '"title": "景点打卡"' in prompt
