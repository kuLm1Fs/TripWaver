from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.llm_prompt import build_itinerary_prompt

request = ItineraryRequest(destination="Shanghai", days=1, interests=["food", "museum"])

candidates = [
    CandidatePlace(name="Shanghai Museum", category="museum", reason="A popular museum in Shanghai")
]

print(build_itinerary_prompt(request, candidates))
