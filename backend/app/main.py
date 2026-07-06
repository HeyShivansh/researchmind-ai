from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(health_router)


@app.get("/")
def root():

    return {
        "message": "Welcome to ResearchMind AI"
    }