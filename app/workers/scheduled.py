"""
Scheduled Celery tasks (run by Celery Beat).
"""
import asyncio
import logging
from sqlalchemy import select, update

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.user import User, PlanType
from app.core.dependencies import get_plan_daily_limit

logger = logging.getLogger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.scheduled.reset_daily_credits")
def reset_daily_credits():
    """
    Resets daily_apps_remaining for ALL users based on their plan.
    Runs every day at 00:00 UTC via Celery Beat.
    """
    run_async(_reset_credits_async())


async def _reset_credits_async():
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        for user in users:
            user.daily_apps_remaining = get_plan_daily_limit(user.plan_type)
            user.last_reset_date = datetime.now(timezone.utc)

        await db.commit()
        logger.info(f"Daily credits reset for {len(users)} users.")
