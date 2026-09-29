"""
Subscriptions / Stripe routes
- POST /checkout  → create Stripe Checkout Session
- POST /webhook   → handle Stripe events (subscription activated, canceled, etc.)
- GET  /me        → current subscription status
- POST /cancel    → cancel at period end
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import get_current_user, get_plan_daily_limit
from app.db.session import get_db
from app.models.user import User, PlanType
from app.models.subscription import Subscription
from app.schemas.common import CheckoutSessionCreate, SubscriptionOut

try:
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
except ImportError:
    stripe = None

router = APIRouter()

PLAN_MAP = {
    "basic": (settings.STRIPE_PRICE_ID_BASIC, PlanType.BASIC),
    "pro":   (settings.STRIPE_PRICE_ID_PRO,   PlanType.PRO),
}


@router.post("/checkout")
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe Checkout Session URL for the chosen plan."""
    if payload.plan not in PLAN_MAP:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'basic' or 'pro'.")

    price_id, _ = PLAN_MAP[payload.plan]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=current_user.email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/dashboard?upgraded=true",
        cancel_url=f"{settings.FRONTEND_URL}/pricing",
        metadata={"user_id": str(current_user.id), "plan": payload.plan},
    )
    return {"checkout_url": session.url}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Stripe webhook — handles subscription lifecycle events."""
    body = await request.body()
    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    data = event["data"]["object"]

    if event["type"] == "checkout.session.completed":
        user_id = int(data["metadata"]["user_id"])
        plan_str = data["metadata"]["plan"]
        sub_id = data.get("subscription")

        plan_type = PLAN_MAP[plan_str][1]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.plan_type = plan_type
            user.stripe_subscription_id = sub_id
            user.daily_apps_remaining = get_plan_daily_limit(plan_type)

            # Upsert Subscription record
            sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
            sub_record = sub_result.scalar_one_or_none()
            stripe_sub = stripe.Subscription.retrieve(sub_id)
            if sub_record:
                sub_record.stripe_subscription_id = sub_id
                sub_record.stripe_price_id = stripe_sub["items"]["data"][0]["price"]["id"]
                sub_record.status = stripe_sub["status"]
            else:
                db.add(Subscription(
                    user_id=user_id,
                    stripe_subscription_id=sub_id,
                    stripe_price_id=stripe_sub["items"]["data"][0]["price"]["id"],
                    status=stripe_sub["status"],
                ))
            await db.commit()

    elif event["type"] in ("customer.subscription.deleted", "customer.subscription.updated"):
        sub_id = data["id"]
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        )
        sub_record = result.scalar_one_or_none()
        if sub_record:
            sub_record.status = data["status"]
            sub_record.cancel_at_period_end = data.get("cancel_at_period_end", False)
            if data["status"] in ("canceled", "unpaid"):
                user_result = await db.execute(select(User).where(User.id == sub_record.user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.plan_type = PlanType.FREE
                    user.daily_apps_remaining = get_plan_daily_limit(PlanType.FREE)
            await db.commit()

    return {"received": True}


@router.get("/me", response_model=SubscriptionOut | None)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    return result.scalar_one_or_none()


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel subscription at period end via Stripe."""
    if not current_user.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")
    stripe.Subscription.modify(
        current_user.stripe_subscription_id,
        cancel_at_period_end=True,
    )
    return {"message": "Subscription will cancel at period end"}
