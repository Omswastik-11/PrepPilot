"""
PrepPilot — FastAPI Application Entry Point.

This is the composition root — where all pieces of the app come together.
main.py should be thin. It only:
  1. Creates the FastAPI app instance
  2. Registers middleware (CORS)
  3. Registers global exception handlers
  4. Includes route modules
  5. Defines startup/shutdown lifecycle hooks

All business logic lives in services → repositories → models.
All auth logic lives in dependencies.py.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine
from app.exceptions import (
    AppException,
    NotFoundError,
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    InvalidStateError,
    AIServiceError,
)
from app.models import Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.

    Code before `yield` runs at STARTUP (create tables, connect to services).
    Code after `yield` runs at SHUTDOWN (close connections, cleanup).

    In production, you'd use Alembic migrations instead of create_all().
    We keep create_all() here for rapid development — it creates tables
    that don't exist but won't modify existing ones.
    """
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print(f"🚀 {settings.APP_NAME} started in {settings.ENVIRONMENT} mode")

    yield

    await engine.dispose()
    print(f"👋 {settings.APP_NAME} shutting down")


# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered interview coaching platform",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Global Exception Handlers
#
# These convert domain exceptions (raised by services) into HTTP responses.
# Services raise AppException subclasses; these handlers translate them
# to the correct HTTP status code and a consistent JSON error format.
# ---------------------------------------------------------------------------

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(InvalidStateError)
async def invalid_state_handler(request: Request, exc: InvalidStateError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(AIServiceError)
async def ai_service_handler(request: Request, exc: AIServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------

from app.routes import auth, interviews, candidate, knowledge  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["Interviews"])
app.include_router(candidate.router)
app.include_router(knowledge.router)


# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Actually check DB connection (Phase 9)
        "version": "0.2.0",
    }
