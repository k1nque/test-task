"""Main FastAPI application."""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import organizations, buildings, activities

# Configure logging
def _resolve_log_level(level_name: str) -> tuple[int, bool]:
    """Resolve a logging level name to its numeric value."""
    level = getattr(logging, level_name.upper(), None)
    if isinstance(level, int):
        return level, False
    return logging.INFO, True


_log_level, _invalid_log_level = _resolve_log_level(settings.LOG_LEVEL)

logging.basicConfig(
    level=_log_level,
    format=settings.LOG_FORMAT,
    datefmt=settings.LOG_DATE_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logging.captureWarnings(True)

for _logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(_logger_name).setLevel(_log_level)

if _invalid_log_level:
    logging.getLogger(__name__).warning(
        "Unknown LOG_LEVEL '%s'. Falling back to INFO.",
        settings.LOG_LEVEL,
    )

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    REST API для справочника Организаций, Зданий и Деятельности.
    
    ## Особенности
    
    * **Организации**: Управление организациями с номерами телефонов и видами деятельности
    * **Здания**: Управление зданиями с географическими координатами
    * **Деятельности**: Древовидная структура видов деятельности (до 3 уровней)
    * **Поиск**: Поиск организаций по зданию, деятельности, названию и географическому местоположению
    
    ## Аутентификация
    
    Все запросы требуют наличия заголовка `X-API-Key` с действительным API ключом.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(buildings.router, prefix=settings.API_V1_PREFIX)
app.include_router(activities.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Organizations Directory API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
