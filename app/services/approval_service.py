"""Persistent approval checkpoints with in-process waiters."""

from __future__ import annotations

import asyncio
from typing import Any

from app.database.dao import approvals as approvals_dao
from app.database.session import session_scope
from app.services.event_bus import get_event_bus
from app.utils.logging import get_logger

log = get_logger(__name__)


class ApprovalService:
    def __init__(self) -> None:
        self._waiters: dict[int, asyncio.Event] = {}
        self._results: dict[int, bool] = {}

    async def create_checkpoint(
        self,
        *,
        application_id: int,
        job_id: int,
        checkpoint_type: str,
        confidence: float | None = None,
        resume_version_id: int | None = None,
        ai_summary: str | None = None,
        risks: list[str] | None = None,
        generated_answers: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> int:
        async with session_scope() as db:
            row = await approvals_dao.create(
                db,
                application_id=application_id,
                job_id=job_id,
                checkpoint_type=checkpoint_type,
                confidence=confidence,
                resume_version_id=resume_version_id,
                ai_summary=ai_summary,
                risks=risks,
                generated_answers=generated_answers,
                payload=payload,
            )
            checkpoint_id = row.id

        get_event_bus().emit(
            "approval.requested",
            {"id": checkpoint_id, "application_id": application_id, "type": checkpoint_type},
        )
        log.info("approval.requested", id=checkpoint_id, type=checkpoint_type)
        return checkpoint_id

    async def wait_for_checkpoint(self, checkpoint_id: int, *, timeout: float | None = None) -> bool:
        event = asyncio.Event()
        self._waiters[checkpoint_id] = event
        try:
            if timeout:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                await event.wait()
        except TimeoutError:
            return False
        finally:
            self._waiters.pop(checkpoint_id, None)
        return self._results.pop(checkpoint_id, False)

    async def approve(self, checkpoint_id: int, *, resolved_by: str = "user") -> bool:
        async with session_scope() as db:
            row = await approvals_dao.get_by_id(db, checkpoint_id)
            if row is None:
                return False
            await approvals_dao.resolve(db, row, status="approved", resolved_by=resolved_by)

        self._results[checkpoint_id] = True
        if checkpoint_id in self._waiters:
            self._waiters[checkpoint_id].set()
        get_event_bus().emit("approval.resolved", {"id": checkpoint_id, "approved": True})
        return True

    async def reject(self, checkpoint_id: int, *, resolved_by: str = "user") -> bool:
        async with session_scope() as db:
            row = await approvals_dao.get_by_id(db, checkpoint_id)
            if row is None:
                return False
            await approvals_dao.resolve(db, row, status="rejected", resolved_by=resolved_by)

        self._results[checkpoint_id] = False
        if checkpoint_id in self._waiters:
            self._waiters[checkpoint_id].set()
        get_event_bus().emit("approval.resolved", {"id": checkpoint_id, "approved": False})
        return True

    async def request_edit(self, checkpoint_id: int) -> bool:
        async with session_scope() as db:
            row = await approvals_dao.get_by_id(db, checkpoint_id)
            if row is None:
                return False
            await approvals_dao.resolve(db, row, status="edit_requested", resolved_by="user")

        self._results[checkpoint_id] = False
        if checkpoint_id in self._waiters:
            self._waiters[checkpoint_id].set()
        get_event_bus().emit("approval.edit_requested", {"id": checkpoint_id})
        return True

    async def pending_count(self) -> int:
        async with session_scope() as db:
            return await approvals_dao.count_pending(db)


_service: ApprovalService | None = None


def get_approval_service() -> ApprovalService:
    global _service
    if _service is None:
        _service = ApprovalService()
    return _service
