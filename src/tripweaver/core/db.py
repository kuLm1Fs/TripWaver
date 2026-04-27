from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from tripweaver.core.config import get_settings

settings = get_settings()

# 异步数据库引擎
engine = create_async_engine(settings.db_url, echo=settings.app_env == "local")

# 异步会话工厂
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ORM基础类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """依赖注入：获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session
