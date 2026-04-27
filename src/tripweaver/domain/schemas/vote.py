from pydantic import BaseModel, Field


class VoteRequest(BaseModel):
    """投票请求"""
    itinerary_id: int
    plan_index: int = Field(ge=0, description="投票选择的方案索引")


class VoteResponse(BaseModel):
    """投票响应"""
    success: bool
    message: str
    itinerary_id: int
    plan_index: int
    vote_stats: list[dict]
