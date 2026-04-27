from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    destination: str = Field(..., description="Destination city or area")
    days: int = Field(default=1, ge=1, le=30)
    interests: list[str] = Field(default_factory=list)


class CandidatePlace(BaseModel):
    name: str
    category: str
    reason: str
    address: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    price: str | None = None
    business_hours: str | None = None
    tags: list[str] = Field(default_factory=list)


class ItineraryItem(BaseModel):
    day: int
    title: str
    summary: str
    places: list[CandidatePlace]


class ItineraryResponse(BaseModel):
    itinerary_id: int | None = None
    destination: str
    overview: str
    items: list[ItineraryItem]
    plan_options: list[dict] = Field(default_factory=list, description="多路线方案选项")
