from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RegisterRequest

LOGIN_ATTEMPTS_PREFIX = "login_attempts:"
LOGIN_BLOCK_SECONDS = 900
MAX_LOGIN_ATTEMPTS = 5
BLACKLIST_PREFIX = "blacklist:"


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def authenticate(self, email: str, password: str) -> tuple[User, str, str]:
        await self._check_login_attempts(email)

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            await self._increment_login_attempts(email)
            raise ValueError("invalid_credentials")

        if not user.is_active:
            raise ValueError("account_inactive")

        await self._reset_login_attempts(email)

        access_token, access_jti = create_access_token(
            str(user.id), {"email": user.email, "role": user.role.value}
        )
        refresh_token, refresh_jti = create_refresh_token(str(user.id))

        await self.redis.setex(
            f"refresh:{refresh_jti}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            str(user.id),
        )

        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[User, str, str]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("invalid_refresh_token")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        stored = await self.redis.get(f"refresh:{jti}")
        if not stored or stored != user_id:
            raise ValueError("invalid_refresh_token")

        await self.redis.delete(f"refresh:{jti}")

        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("user_not_found")

        access_token, _ = create_access_token(
            str(user.id), {"email": user.email, "role": user.role.value}
        )
        new_refresh, new_jti = create_refresh_token(str(user.id))

        await self.redis.setex(
            f"refresh:{new_jti}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            str(user.id),
        )

        return user, access_token, new_refresh

    async def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        payload = decode_token(access_token)
        if payload and payload.get("jti"):
            exp = payload.get("exp", 0)
            now = datetime.now(UTC).timestamp()
            ttl = max(int(exp - now), 0)
            if ttl > 0:
                await self.redis.setex(f"{BLACKLIST_PREFIX}{payload['jti']}", ttl, "1")

        if refresh_token:
            r_payload = decode_token(refresh_token)
            if r_payload and r_payload.get("jti"):
                await self.redis.delete(f"refresh:{r_payload['jti']}")

    async def register(self, data: RegisterRequest) -> User:
        if not validate_password(data.password):
            raise ValueError("weak_password")

        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("email_taken")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            patronymic=data.patronymic,
            position=data.position,
            telegram_username=data.telegram_username,
            is_active=False,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def _check_login_attempts(self, email: str) -> None:
        key = f"{LOGIN_ATTEMPTS_PREFIX}{email}"
        attempts = await self.redis.get(key)
        if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
            raise ValueError("account_locked")

    async def _increment_login_attempts(self, email: str) -> None:
        key = f"{LOGIN_ATTEMPTS_PREFIX}{email}"
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_BLOCK_SECONDS)
        await pipe.execute()

    async def _reset_login_attempts(self, email: str) -> None:
        await self.redis.delete(f"{LOGIN_ATTEMPTS_PREFIX}{email}")
