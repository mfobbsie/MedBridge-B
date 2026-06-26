"""
app/main.py — Caduceus Decision-App API entry point.

Assembles the FastAPI application:
    - App-level metadata (title, description, version, contact, tags)
    - Exception handlers (NotFoundException, DuplicateException, ForbiddenException)
    - CORS middleware (Streamlit :8501, Next.js :3000)
    - Rate limiting via slowapi
    - All routers (auth, decisions, securities, coverage)
    - Startup event: creates tables for SQLite (dev/test); Alembic handles Postgres

Run: uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import engine, Base
from app.exceptions import register_exception_handlers
from app.routers import auth, decisions, securities

settings = get_settings()

# ---------------------------------------------------------------------------
# Rate limiter (slowapi)
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables for SQLite (dev/test).
    # In production, Alembic migrations handle schema changes — never call
    # create_all() against Supabase Postgres in production.
    if settings.database_url.startswith("sqlite"):
        import app.models  # ensure all models are registered on Base.metadata
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nothing to clean up yet


# ---------------------------------------------------------------------------
# OpenAPI tags (appear as sections in Swagger UI)
# ---------------------------------------------------------------------------

TAGS_METADATA = [
    {
        "name": "Auth",
        "description": (
            "Analyst authentication. Register an account, log in to receive a JWT, "
            "and retrieve your own profile. The JWT is required for all other endpoints."
        ),
    },
    {
        "name": "Decisions",
        "description": (
            "The decision registry — the core of Caduceus. "
            "Analysts record investment calls (Buy/Add/Hold/Trim/Sell) with conviction, "
            "rationale, pinned evidence, and a workflow breadcrumb that captures *how* "
            "the decision was reached. All decisions are readable firm-wide; write access "
            "is restricted to the decision's author."
        ),
    },
    {
        "name": "Securities",
        "description": (
            "Read-only access to the Caduceus security universe. "
            "Securities are owned by the data pipeline (EDGAR canonical source) — "
            "this API surfaces them for query but never exposes write endpoints."
        ),
    },
    {
        "name": "Coverage",
        "description": (
            "Analyst coverage assignments — which analyst covers which ticker. "
            "Coverage is analyst-managed (not pipeline-managed), so this is a "
            "full CRUD resource."
        ),
    },
]


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Caduceus Decision API",
    description=(
        "## Healthcare Equity Decision-Support Platform\n\n"
        "The Caduceus Decision API is the backend for the Rhenman & Partners "
        "healthcare equity decision-support platform. It centralizes analyst "
        "investment decisions, provides firm-wide visibility into the decision "
        "registry, and exposes an AI-ready endpoint for evidence-backed suggestions "
        "(RAG pipeline in Modules 7-8).\n\n"
        "**Phase 1 universe:** PFE, MRK, JNJ, ABBV, BMY, LLY, AMGN, GILD\n\n"
        "**Auth:** All endpoints except `/auth/register` and `/auth/login` require "
        "a Bearer JWT token. Use the 🔓 Authorize button above to authenticate."
    ),
    version="0.1.0",
    contact={
        "name": "Kathy Matosli — Quant Developer",
        "email": "kathy@rhenman.com",
    },
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware — CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # localhost:8501 (Streamlit) + localhost:3000 (Next.js)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

register_exception_handlers(app)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(decisions.router)
app.include_router(securities.router)
# Coverage router added in next build step


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"], summary="API health check")
def health():
    """Returns API status and version. No auth required."""
    return {
        "status": "ok",
        "api": "Caduceus Decision API",
        "version": "0.1.0",
        "docs": "/docs",
    }
