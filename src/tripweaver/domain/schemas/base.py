from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=100, description="目的地（城市或区域）")
    days: int = Field(default=1, ge=1, le=30, description="游玩天数")
    interests: list[str] = Field(default_factory=list, max_length=10, description="兴趣偏好标签")
    latitude: float | None = Field(default=None, description="纬度（高德地图）")
    longitude: float | None = Field(default=None, description="经度（高德地图）")
    address: str | None = Field(default=None, description="地理编码后的标准地址")
    range_mode: str = Field(default="walking", description="范围模式：walking 或 transit")
    range_minutes: int = Field(default=20, ge=5, le=120, description="可达范围时间（分钟）")
    custom_tags: list[str] = Field(default_factory=list, max_length=20, description="用户自定义标签")


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
