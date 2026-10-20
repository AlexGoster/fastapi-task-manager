"""JWT authentication utilities."""

from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = settings.algorithm
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


def create_access_token(data: dict[str, object], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return cast(str, jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM))


def decode_access_token(token: str) -> dict[str, object] | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        return cast(dict[str, object], payload)
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    try:
        subject = payload.get("sub") if payload else None
        user_id = int(subject) if isinstance(subject, str) else 0
    except (ValueError, TypeError, KeyError):
        user_id = 0
    if not 0 < user_id <= 2_147_483_647:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user
