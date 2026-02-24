"""
Job Assistant API - Production-grade FastAPI application.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import config
from core.logging import setup_logging, get_logger
from core.errors import validation_exception_handler, generic_exception_handler
from core.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from core.limiter import setup_rate_limiting
from db.database import init_db
from routers import auth, profile, chat, threads

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    setup_logging(debug=config.DEBUG)
    logger.info("Initializing database")
    init_db()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None,
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Rate limiting
setup_rate_limiting(app)

# Middleware order: first added = last executed (innermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Authorization"],
)

app.include_router(auth.router, prefix=config.API_PREFIX)
app.include_router(profile.router, prefix=config.API_PREFIX)
app.include_router(chat.router, prefix=config.API_PREFIX)
app.include_router(threads.router, prefix=config.API_PREFIX)


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok", "version": config.API_VERSION}


@app.get("/api/health", tags=["health"])
def api_health():
    """API health check (same as /health)."""
    return {"status": "ok", "version": config.API_VERSION}


# --- Serve frontend ---

logger.info(f"Frontend directory: {FRONTEND_DIR} (exists={FRONTEND_DIR.exists()})")


@app.get("/", tags=["frontend"])
def serve_index():
    """Serve the test frontend."""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index, media_type="text/html")
    return {"detail": "Frontend not found", "path": str(index)}


@app.get("/auth/callback", tags=["frontend"])
def auth_callback_page():
    """Serve frontend for OAuth callback (tokens come as query params)."""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index, media_type="text/html")
    return {"detail": "Frontend not found", "path": str(index)}
