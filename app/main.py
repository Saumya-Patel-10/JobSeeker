"""
JobAIgent — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.routes import auth, users, resumes, jobs, applications, subscriptions, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered job application assistant API",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,          prefix="/api/v1/auth",          tags=["Auth"])
app.include_router(users.router,         prefix="/api/v1/users",         tags=["Users"])
app.include_router(resumes.router,       prefix="/api/v1/resumes",       tags=["Resumes"])
app.include_router(jobs.router,          prefix="/api/v1/jobs",          tags=["Jobs"])
app.include_router(applications.router,  prefix="/api/v1/applications",  tags=["Applications"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])
app.include_router(websocket.router,     prefix="/ws",                   tags=["WebSocket"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
