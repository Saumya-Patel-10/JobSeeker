from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import oauth2_scheme, decode_access_token
from app.db.session import get_db
from app.models.user import User, PlanType
from app.core.config import settings


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT and return the User ORM object."""
    from sqlalchemy import select

    token_data = decode_access_token(token)
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    return user


def require_credits(func):
    """
    Middleware decorator — checks daily_apps_remaining > 0
    before allowing tailor_resume / apply_job routes to proceed.
    Usage: @require_credits  (applied on the route function)
    """
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
        if current_user.daily_apps_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Daily application limit reached for your "
                    f"{current_user.plan_type.value} plan. "
                    "Upgrade or wait until tomorrow."
                ),
            )
        return await func(*args, current_user=current_user, **kwargs)

    return wrapper


def get_plan_daily_limit(plan: PlanType) -> int:
    """Return the configured daily limit for a given plan."""
    limits = {
        PlanType.FREE:  settings.PLAN_FREE_DAILY_LIMIT,
        PlanType.BASIC: settings.PLAN_BASIC_DAILY_LIMIT,
        PlanType.PRO:   settings.PLAN_PRO_DAILY_LIMIT,
    }
    return limits[plan]
