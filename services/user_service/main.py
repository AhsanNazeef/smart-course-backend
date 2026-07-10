"""User service - standalone FastAPI application.

This is its OWN app (separate from the monolith), runnable independently:

    uvicorn services.user_service.main:app --port 8001

It owns its database (users_db) and exposes the user API. Other services
never import this module - they talk to it over HTTP or via its events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.user_service.config import settings
from services.user_service.database import check_connection, engine
from services.user_service.router import router as user_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    try:
        await check_connection()
        logger.info("User service database connection OK")
    except Exception as exc:  # noqa: BLE001 - log and continue; /health stays up
        logger.warning(f"User service database not reachable at startup: {exc}")
    yield
    await engine.dispose()
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="SmartCourse User Service - owns users and authentication data",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
    }


app.include_router(user_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.user_service.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
