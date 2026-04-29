from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status

from tripweaver.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """生成JWT访问令牌"""
    to_encode = {
        "sub": str(user_id),
        "type": TOKEN_TYPE_ACCESS,
    }
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """生成JWT刷新令牌（有效期7天）"""
    to_encode = {
        "sub": str(user_id),
        "type": TOKEN_TYPE_REFRESH,
    }
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(token: str, expected_type: str = TOKEN_TYPE_ACCESS) -> int:
    """验证JWT令牌，返回用户ID"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="令牌无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", TOKEN_TYPE_ACCESS)
        if user_id is None or token_type != expected_type:
            raise credentials_exception
        return int(user_id)
    except jwt.PyJWTError:
        raise credentials_exception
