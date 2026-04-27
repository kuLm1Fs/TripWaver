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
    assert "优先使用候选地点" in prompt
    assert "只能返回合法 JSON" in prompt
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
