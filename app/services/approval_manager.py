import asyncio
from typing import Any

from app.utils.logging import get_logger

log = get_logger(__name__)

class ApprovalManager:
    """Manages human-in-the-loop approval checkpoints."""
    def __init__(self):
        self._approvals: dict[str, asyncio.Event] = {}
        self._results: dict[str, bool] = {}
        self._payloads: dict[str, dict[str, Any]] = {}

    async def wait_for_approval(self, approval_id: str, payload: dict[str, Any]) -> bool:
        from app.services.event_bus import get_event_bus
        event = asyncio.Event()
        self._approvals[approval_id] = event
        self._payloads[approval_id] = payload

        log.info("approval.requested", id=approval_id)
        get_event_bus().emit("approval.requested", {"id": approval_id, "payload": payload})

        await event.wait()

        result = self._results.pop(approval_id, False)
        log.info("approval.resolved", id=approval_id, approved=result)
        return result

    def approve(self, approval_id: str):
        if approval_id in self._approvals:
            self._results[approval_id] = True
            self._approvals[approval_id].set()

    def reject(self, approval_id: str):
        if approval_id in self._approvals:
            self._results[approval_id] = False
            self._approvals[approval_id].set()

    def get_pending(self) -> list[dict[str, Any]]:
        return [
            {"id": aid, "payload": self._payloads[aid]}
            for aid in self._approvals
        ]

_manager = ApprovalManager()

def get_approval_manager() -> ApprovalManager:
    return _manager
