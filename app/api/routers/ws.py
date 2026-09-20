from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.runtime.automation_runtime import get_automation_runtime
from app.runtime.discovery_scheduler import get_discovery_scheduler
from app.services.approval_service import get_approval_service
from app.services.event_bus import get_event_bus
from app.utils.logging import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self._send_snapshot(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _send_snapshot(self, websocket: WebSocket) -> None:
        pending = await get_approval_service().pending_count()
        snapshot = {
            "type": "runtime.snapshot",
            "payload": {
                "automation": get_automation_runtime()
                .snapshot(pending_approval_count=pending)
                .model_dump(mode="json"),
                "discovery": get_discovery_scheduler().status().model_dump(mode="json"),
            },
        }
        await websocket.send_text(json.dumps(snapshot))

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


async def event_bus_to_ws(event_type: str, payload: dict[str, Any]):
    message = json.dumps({"type": event_type, "payload": payload})
    await manager.broadcast(message)


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "payload": {}}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
