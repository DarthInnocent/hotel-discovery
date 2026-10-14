from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.controllers.shortlist_controller import get_shortlist_controller
from app.api.endpoints import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on startup
    get_shortlist_controller().initialize_database()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI service for U.S. ZIP code geocoding, 5km hotel discovery via Geoapify, and persistent shortlist.",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
async def health_check() -> dict[str, object]:
    has_key = bool(settings.GEOAPIFY_API_KEY and settings.GEOAPIFY_API_KEY != "your_geoapify_api_key_here")
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "geoapify_configured": has_key,
    }

@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to Hotel Discovery API. Visit /docs for interactive Swagger UI.",
    }
