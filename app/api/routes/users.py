"""Users routes — profile, plan reset, daily credits."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, PlanType
from app.schemas.auth import UserOut
from app.core.dependencies import get_current_user, get_plan_daily_limit

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/plan", response_model=UserOut)
async def update_plan(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user plan (called after Stripe checkout success)."""
    try:
        new_plan = PlanType(plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan")

    current_user.plan_type = new_plan
    current_user.daily_apps_remaining = get_plan_daily_limit(new_plan)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post("/me/reset-credits", response_model=UserOut)
async def reset_credits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually reset daily credits (normally done by Celery Beat at midnight).
    Admin / testing endpoint.
    """
    current_user.daily_apps_remaining = get_plan_daily_limit(current_user.plan_type)
    await db.commit()
    await db.refresh(current_user)
    return current_user
