from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from tripweaver.core.config import get_settings

settings = get_settings()

# 异步数据库引擎
engine = create_async_engine(
    settings.db_url,
    echo=settings.app_env == "local",
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # 拿连接前先验证连通性
    pool_recycle=3600,  # 1小时回收连接，避免连接过期
)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ORM基础类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """依赖注入：获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session
