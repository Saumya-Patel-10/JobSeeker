from typing import Optional
from pydantic import BaseModel

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore[assignment, misc]


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    plan_type: str = "free"   # "free" | "basic" | "pro"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    plan_type: str
    daily_apps_remaining: int
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
