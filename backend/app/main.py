"""
Main FastAPI application for Barclays Credit Intelligence Platform
Production-grade credit scoring system for unbanked populations
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from importlib import import_module

from app.core.config import settings
from app.core.logging import logger
from app.core.database import check_database_connection, engine
from app.api.routes import applications, auth, admin, chat
from app.ml.predict import CreditScorer
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown events
    """
    # ─── STARTUP ───────────────────────────────────────────────────────────
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION}",
        extra={
            'environment': settings.ENVIRONMENT,
            'debug': settings.DEBUG,
            'database': settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'unknown'
        }
    )
    
    app.state.db_ready = False
    app.state.redis_ready = False
    app.state.ml_ready = False
    app.state.redis_client = None

    # Initialize database connectivity
    try:
        app.state.db_ready = check_database_connection()
        if not app.state.db_ready:
            raise RuntimeError("Database ping failed")
        # Bootstrap tables for local/dev runs when migrations are not yet wired.
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection established", extra={'status': 'connected'})
    except Exception as e:
        logger.error("Failed to connect to database", extra={'error': str(e)})
        raise
    
    # Initialize Redis cache
    try:
        redis_mod = import_module("redis")
        app.state.redis_client = redis_mod.from_url(settings.REDIS_URL, decode_responses=True)
        app.state.redis_ready = bool(app.state.redis_client.ping())
        logger.info("Redis cache initialized", extra={'status': 'connected'})
    except Exception as e:
        app.state.redis_ready = False
        logger.error("Failed to connect to Redis", extra={'error': str(e)})
        # Don't raise - Redis is optional for some operations
    
    # Load ML model into memory
    try:
        scorer = CreditScorer()
        model_path = applications._resolve_winner_contract_model()
        scorer.load_model(model_path)
        app.state.ml_scorer = scorer
        applications._SCORER = scorer
        app.state.ml_ready = True
        logger.info("ML model loaded", extra={'model_version': settings.ML_MODEL_VERSION})
    except Exception as e:
        app.state.ml_ready = False
        logger.error("Failed to load ML model", extra={'error': str(e)})
        if settings.ENVIRONMENT == "production":
            raise
    
    yield
    
    # ─── SHUTDOWN ──────────────────────────────────────────────────────────
    logger.info(f"Shutting down {settings.APP_NAME}")
    if getattr(app.state, "redis_client", None) is not None:
        app.state.redis_client.close()


def create_app() -> FastAPI:
    """
    FastAPI application factory.
    
    Returns:
        Configured FastAPI application instance
    """
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered credit intelligence platform for unbanked populations",
        version=settings.APP_VERSION,
        docs_url=settings.DOCS_URL if settings.DEBUG else None,
        openapi_url=settings.OPENAPI_URL if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # ─── MIDDLEWARE ────────────────────────────────────────────────────────
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Dev frontend
            "http://localhost:8000",  # Dev backend
            "https://barclays-credit.com",  # Production domain
        ] if settings.ENVIRONMENT == "production" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests and responses"""
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'ip': request.client.host if request.client else "unknown"
            }
        )
        
        # Call endpoint
        response = await call_next(request)
        
        # Log response
        logger.info(
            f"Response: {response.status_code}",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'method': request.method,
                'path': request.url.path
            }
        )
        
        return response
    
    # ─── HEALTH CHECK ──────────────────────────────────────────────────────
    
    @app.get("/api/v1/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        Returns system status and dependency connectivity.
        """
        return {
            "status": "healthy" if (app.state.db_ready and app.state.ml_ready) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if app.state.db_ready else "disconnected",
            "redis": "connected" if app.state.redis_ready else "disconnected",
            "ml_model": "loaded" if app.state.ml_ready else "not_loaded"
        }
    
    # ─── ROUTES ────────────────────────────────────────────────────────────
    
    # Include route modules
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
    # app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["Users"])
    app.include_router(applications.router, prefix=settings.API_V1_PREFIX, tags=["Applications"])
    # app.include_router(scoring.router, prefix=settings.API_V1_PREFIX, tags=["Scoring"])
    app.include_router(admin.router, prefix=settings.API_V1_PREFIX, tags=["Admin"])
    app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["Chat"])
    # app.include_router(analytics.router, prefix=settings.API_V1_PREFIX, tags=["Analytics"])
    
    # ─── ERROR HANDLERS ────────────────────────────────────────────────────
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                'error_type': type(exc).__name__,
                'path': request.url.path,
                'method': request.method
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.DEBUG else "An error occurred",
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
