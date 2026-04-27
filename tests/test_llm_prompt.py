from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.llm_prompt import build_itinerary_prompt


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
    assert '"plan_name"' in prompt
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
