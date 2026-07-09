from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from shared.config.settings import settings
from services.user_service.router import router as user_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="SmartCourse - Intelligent Course Delivery Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/metrics", make_asgi_app())

# Domain routers
app.include_router(user_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to SmartCourse API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# API v1 router placeholder
@app.get(f"{settings.API_V1_PREFIX}")
async def api_v1_root():
    return {
        "message": "SmartCourse API v1",
        "version": "0.1.0",
        "endpoints": {
            "courses": f"{settings.API_V1_PREFIX}/courses",
            "users": f"{settings.API_V1_PREFIX}/users",
            "enrollments": f"{settings.API_V1_PREFIX}/enrollments",
            "analytics": f"{settings.API_V1_PREFIX}/analytics",
            "ai": f"{settings.API_V1_PREFIX}/ai"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
