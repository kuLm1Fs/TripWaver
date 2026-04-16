from fastapi import FastAPI

from tripweaver.api.routes.itineraries import router as itineraries_router

app = FastAPI(title="TripWeaver")

app.include_router(itineraries_router, prefix="/api/v1")
