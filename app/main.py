"""Application entry point.

Creates the FastAPI app, wires in the routers, and (for development convenience)
auto-creates database tables on startup.

NOTE: `Base.metadata.create_all()` is fine for learning, but real projects use a
migration tool (Alembic) to evolve the schema safely. We'll get there later.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import models  # noqa: F401  -- ensures all ORM models are registered
from app.api.routes import admin, auth, dashboard, health, incidents
from app.core.config import settings
from app.core.limiter import limiter
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    Base.metadata.create_all(bind=engine)  # create tables if they don't exist
    # Security check: warn loudly if the signing key was never changed (Phase 21).
    if settings.SECRET_KEY == "dev-only-insecure-change-me":
        logging.warning(
            "SECURITY: SECRET_KEY is the insecure default — set a strong "
            "SECRET_KEY in your environment before deploying to production!"
        )
    yield
    # ---- shutdown ---- (nothing to clean up yet)


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Rate limiting (Phase 21): register the limiter, its error handler, middleware.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Register routers (each maps to a REST resource from Phase 4's design).
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# Auto-instrument HTTP metrics (request count, latency, status codes) and
# expose everything — including our custom metrics — at GET /metrics.
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}
