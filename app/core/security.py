from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import base64
import hmac
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.schemas.auth import TokenData

try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    JWTError = Exception
    jwt = None
    pwd_context = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    if pwd_context is not None:
        return pwd_context.hash(plain)
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    if pwd_context is not None:
        try:
            return pwd_context.verify(plain, hashed)
        except Exception:
            pass
    return hashlib.sha256(plain.encode("utf-8")).hexdigest() == hashed


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire.timestamp() if jwt is None else expire})
    if jwt is not None:
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    # Simple signed token fallback if python-jose is not installed locally
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    sig = hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def decode_access_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if jwt is not None:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            return TokenData(user_id=int(user_id))
        # Simple token decoder fallback
        parts = token.split(".")
        if len(parts) != 2:
            raise credentials_exception
        payload_b64, sig = parts
        expected_sig = hmac.new(settings.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise credentials_exception
        pad = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return TokenData(user_id=int(user_id))
    except Exception:
        raise credentials_exception
