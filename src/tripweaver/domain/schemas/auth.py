
from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(pattern=r"^1[3-9]\d{9}$", description="手机号")


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(min_length=6, max_length=6, description="验证码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    nickname: str | None
    avatar: str | None
