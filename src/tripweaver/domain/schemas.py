from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    destination: str = Field(..., description="Destination city or area")
    days: int = Field(default=1, ge=1, le=30)
    interests: list[str] = Field(default_factory=list)


class CandidatePlace(BaseModel):
    name: str
    category: str
    reason: str


class ItineraryItem(BaseModel):
    day: int
    title: str
    summary: str
    places: list[CandidatePlace]


class ItineraryResponse(BaseModel):
    destination: str
    overview: str
    items: list[ItineraryItem]
