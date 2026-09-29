"""Import all models here so Alembic & Base.metadata.create_all() can discover them."""
from app.db.base_class import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
