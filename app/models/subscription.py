"""Subscription model — mirrors Stripe subscription state (ORM only)."""

from __future__ import annotations

# ── SQLAlchemy ORM model ─────────────────────────────────────────────────────

try:
    from datetime import datetime as _dt

    from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.db.base_class import Base as _Base  # type: ignore[import]

    class Subscription(_Base):  # type: ignore[valid-type]
        __tablename__ = "subscriptions"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

        stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
        stripe_price_id: Mapped[str] = mapped_column(String(255), nullable=False)
        status: Mapped[str] = mapped_column(String(64), nullable=False)
        current_period_end: Mapped[_dt | None] = mapped_column(DateTime(timezone=True), nullable=True)
        cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)

        created_at: Mapped[_dt] = mapped_column(DateTime(timezone=True), server_default=func.now())
        updated_at: Mapped[_dt] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

        user: Mapped[object] = relationship("User", back_populates="subscription")

except Exception:
    Subscription = None  # type: ignore[assignment, misc]
