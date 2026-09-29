"""User model — ORM table + PlanType enum.

``PlanType`` — string enum for subscription plan (free / basic / pro).
``User``     — SQLAlchemy ORM row (guarded import).
"""

from __future__ import annotations

import enum


class PlanType(str, enum.Enum):
    FREE  = "free"
    BASIC = "basic"   # $3.99
    PRO   = "pro"     # $7.99


# ── SQLAlchemy ORM model ─────────────────────────────────────────────────────

try:
    from datetime import datetime as _dt

    from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.db.base_class import Base as _Base  # type: ignore[import]

    class User(_Base):  # type: ignore[valid-type]
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
        email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
        full_name: Mapped[str] = mapped_column(String(255), nullable=False)
        hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

        plan_type: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
        daily_apps_remaining: Mapped[int] = mapped_column(Integer, default=12)
        last_reset_date: Mapped[_dt] = mapped_column(DateTime(timezone=True), default=func.now())

        stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
        stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

        created_at: Mapped[_dt] = mapped_column(DateTime(timezone=True), server_default=func.now())
        updated_at: Mapped[_dt] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

        resumes: Mapped[list] = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")  # type: ignore[type-arg]
        applications: Mapped[list] = relationship("Application", back_populates="user", cascade="all, delete-orphan")  # type: ignore[type-arg]
        subscription: Mapped[object] = relationship("Subscription", back_populates="user", uselist=False)

except Exception:
    User = None  # type: ignore[assignment, misc]
