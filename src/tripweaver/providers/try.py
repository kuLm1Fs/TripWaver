# from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
# from tripweaver.providers.llm_prompt import build_itinerary_prompt

# request = ItineraryRequest(destination="Shanghai", days=1, interests=["food", "museum"])

# candidates = [
#    CandidatePlace(name="Shanghai Museum", category="museum", reason="A popular museum in Shanghai")
# ]

# print(build_itinerary_prompt(request, candidates))

import asyncio

from tripweaver.core.config import get_settings
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.llm import ARKLLMProvider


async def main() -> None:
    settings = get_settings()

    provider = ARKLLMProvider(settings)

    request = ItineraryRequest(
        destination="Shanghai",
        days=1,
        interests=["food", "museum"],
    )

    candidates = [
        CandidatePlace(
            name="Shanghai Museum",
            category="museum",
            reason="A popular museum in Shanghai",
        ),
        CandidatePlace(
            name="Yu Garden",
            category="landmark",
            reason="A classic landmark area in Shanghai",
        ),
    ]

    result = await provider.generate_itinerary(request, candidates)
    print(result.model_dump())


asyncio.run(main())
