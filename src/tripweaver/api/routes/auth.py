from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tripweaver.core.db import get_db
from tripweaver.core.security import create_access_token
from tripweaver.domain.schemas.auth import LoginRequest, LoginResponse, SendCodeRequest
from tripweaver.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])

# 固定测试验证码
TEST_VERIFICATION_CODE = "123456"


@router.post("/send-code", summary="发送验证码")
async def send_code(request: SendCodeRequest):
    """发送验证码（开发环境固定返回123456）"""
    return {
        "success": True,
        "message": f"验证码已发送，测试环境固定验证码：{TEST_VERIFICATION_CODE}"
    }


@router.post("/login", response_model=LoginResponse, summary="手机号验证码登录")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """手机号验证码登录，用户不存在自动创建"""
    # 验证码校验
    if request.code != TEST_VERIFICATION_CODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )
    
    # 查询用户是否存在
    result = await db.execute(select(User).where(User.phone == request.phone))
    user = result.scalar_one_or_none()
    
    if not user:
        # 自动创建新用户
        user = User(
            phone=request.phone,
            nickname=f"用户{request.phone[-4:]}"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()
    
    # 生成JWT token
    access_token = create_access_token(user.id)
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        nickname=user.nickname,
        avatar=user.avatar
    )
