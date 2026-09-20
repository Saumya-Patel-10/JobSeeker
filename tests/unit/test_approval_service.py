"""Tests for approval checkpoint service."""

from __future__ import annotations

import pytest

from app.database.engine import reset_for_tests
from app.services.approval_service import ApprovalService


@pytest.mark.asyncio
async def test_approval_checkpoint_create_and_resolve():
    await reset_for_tests()
    service = ApprovalService()
    cid = await service.create_checkpoint(
        application_id=1,
        job_id=1,
        checkpoint_type="pre_submit",
        ai_summary="Test summary",
        risks=["low confidence"],
    )
    assert cid > 0

    async def approve_later():
        import asyncio

        await asyncio.sleep(0.05)
        await service.approve(cid)

    import asyncio

    waiter = asyncio.create_task(service.wait_for_checkpoint(cid, timeout=2.0))
    approver = asyncio.create_task(approve_later())
    result = await waiter
    await approver
    assert result is True
