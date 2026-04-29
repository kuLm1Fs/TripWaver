from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from tripweaver.api.routes.auth import router as auth_router
from tripweaver.api.routes.itineraries import router as itineraries_router
from tripweaver.api.routes.itinerary_ext import router as itinerary_ext_router
from tripweaver.api.routes.cache_admin import router as cache_admin_router
from tripweaver.core.body_limit import BodySizeLimitMiddleware
from tripweaver.core.config import get_settings
from tripweaver.core.errors import register_error_handlers
from tripweaver.core.logging import LoggingMiddleware, setup_logging

setup_logging()

settings = get_settings()
app = FastAPI(title="TripWeaver")

app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(itineraries_router, prefix="/api/v1")
app.include_router(itinerary_ext_router, prefix="/api/v1")
app.include_router(cache_admin_router, prefix="/api/v1")


@app.get("/health/live", summary="存活检查")
async def health_live():
    """Liveness probe — 应用进程存活即可。"""
    from tripweaver.core.health import health_live as check
    return await check()


@app.get("/health/ready", summary="就绪检查")
async def health_ready():
    """Readiness probe — 检查 Redis 和 DB 连通性。"""
    from tripweaver.core.health import health_ready as check
    error_resp, body = await check()
    if error_resp:
        return error_resp
    return body


@app.get("/health", include_in_schema=False)
async def health_check():
    """兼容旧路径。"""
    return {"status": "ok"}
