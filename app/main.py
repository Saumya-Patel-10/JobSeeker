"""
JobSeeker — FastAPI Application Entry Point.
Exports the unified application supporting both local supervision and cloud workers.
"""
from app.api.main import app

__all__ = ["app"]
