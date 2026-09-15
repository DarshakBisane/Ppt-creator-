"""FastAPI application factory and main entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app import __version__
from backend.app.api.health import router as health_router
from backend.app.config import Settings, get_settings
from backend.app.core.errors import register_exception_handlers
from backend.app.logging_config import setup_logging
from backend.app.middleware.request_id import RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle events management."""
    # Startup tasks
    yield
    # Shutdown tasks


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application instance."""
    if settings is None:
        settings = get_settings()

    # Initialize structured logging
    setup_logging(
        log_level=settings.log_level,
        json_logs=settings.is_production,
    )

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Production AI Presentation Generator API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.state.settings = settings

    # 1. Register Request ID Middleware (outer layer)
    app.add_middleware(RequestIdMiddleware)

    # 2. Register CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 3. Register Global Exception Handlers
    register_exception_handlers(app)

    # 4. Register Routers
    app.include_router(health_router)

    return app


# Application instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    current_settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=current_settings.api_host,
        port=current_settings.api_port,
        reload=current_settings.is_development,
    )
