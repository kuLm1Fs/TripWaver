from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tripweaver.api.routes.auth import router as auth_router
from tripweaver.api.routes.itineraries import router as itineraries_router
from tripweaver.api.routes.itinerary_ext import router as itinerary_ext_router
from tripweaver.core.config import get_settings
from tripweaver.core.logging import LoggingMiddleware, setup_logging

setup_logging()

settings = get_settings()
app = FastAPI(title="TripWeaver")

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(itineraries_router, prefix="/api/v1")
app.include_router(itinerary_ext_router, prefix="/api/v1")


@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "ok"}
