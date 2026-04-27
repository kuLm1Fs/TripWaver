from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status

from tripweaver.core.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """生成JWT访问令牌"""
    to_encode = {"sub": str(user_id)}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> int:
    """验证JWT令牌，返回用户ID"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except jwt.PyJWTError:
        raise credentials_exception
