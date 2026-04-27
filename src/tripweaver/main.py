from fastapi import FastAPI

from tripweaver.api.routes.auth import router as auth_router
from tripweaver.api.routes.itineraries import router as itineraries_router
from tripweaver.api.routes.itinerary_ext import router as itinerary_ext_router
from tripweaver.core.logging import LoggingMiddleware, setup_logging

setup_logging()

app = FastAPI(title="TripWeaver")

app.add_middleware(LoggingMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(itineraries_router, prefix="/api/v1")
app.include_router(itinerary_ext_router, prefix="/api/v1")


@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "ok"}
