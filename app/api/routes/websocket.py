"""
WebSocket route — real-time application status updates.
Clients connect to ws://host/ws/applications/{application_id}
and receive JSON status events as Celery workers progress.
"""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.application import Application

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections keyed by application_id."""

    def __init__(self):
        # application_id → list of connected websockets
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, application_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(application_id, []).append(websocket)

    def disconnect(self, application_id: int, websocket: WebSocket):
        conns = self.active.get(application_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast(self, application_id: int, message: dict):
        """Send a JSON message to all listeners on this application."""
        for ws in self.active.get(application_id, []):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/applications/{application_id}")
async def application_status_ws(
    websocket: WebSocket,
    application_id: int,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint.
    Clients pass their JWT as a query param: ?token=<jwt>
    Polls the DB every 3 seconds and pushes status changes.
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001)
        return
    try:
        token_data = decode_access_token(token)
    except Exception:
        await websocket.close(code=4003)
        return

    await manager.connect(application_id, websocket)
    last_status = None

    try:
        while True:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Application).where(
                        Application.id == application_id,
                        Application.user_id == token_data.user_id,
                    )
                )
                app = result.scalar_one_or_none()

            if app is None:
                await websocket.send_text(json.dumps({"error": "Application not found"}))
                break

            if app.status != last_status:
                last_status = app.status
                await websocket.send_text(json.dumps({
                    "application_id": app.id,
                    "status": app.status,
                    "match_score": app.match_score,
                    "message": _status_message(app.status),
                }))

            if app.status in ("submitted", "failed", "skipped"):
                break   # Terminal state — close connection

            await asyncio.sleep(3)

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(application_id, websocket)


def _status_message(status: str) -> str:
    messages = {
        "queued":    "Your application is in the queue...",
        "tailoring": "AI is tailoring your resume to this job...",
        "applying":  "Bot is currently filling out your application form...",
        "submitted": "Application successfully submitted! ✅",
        "failed":    "Something went wrong during the application. ❌",
        "skipped":   "Job skipped — match score too low.",
    }
    return messages.get(status, status)
