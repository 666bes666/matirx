from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenRefreshResponse,
    UserBrief,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_429 = status.HTTP_429_TOO_MANY_REQUESTS
_422 = status.HTTP_422_UNPROCESSABLE_ENTITY
_401 = status.HTTP_401_UNAUTHORIZED

ERROR_MAP = {
    "invalid_credentials": (_401, "Неверный email или пароль"),
    "account_inactive": (status.HTTP_403_FORBIDDEN, "Учётная запись не активирована"),
    "account_locked": (_429, "Попробуйте через 15 минут"),
    "invalid_refresh_token": (_401, "Недействительный refresh token"),
    "user_not_found": (_401, "Пользователь не найден"),
    "weak_password": (_422, "Мин. 8 символов, 1 буква и 1 цифра"),
    "email_taken": (status.HTTP_409_CONFLICT, "Email уже зарегистрирован"),
}


def _raise(code: str) -> None:
    status_code, detail = ERROR_MAP.get(code, (400, code))
    raise HTTPException(status_code=status_code, detail=detail)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    try:
        user, access_token, refresh_token = await service.authenticate(data.email, data.password)
    except ValueError as e:
        _raise(str(e))

    is_secure = settings.ENVIRONMENT != "development"
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=is_secure,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserBrief.model_validate(user),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    try:
        user = await service.register(data)
    except ValueError as e:
        _raise(str(e))

    msg = "Регистрация отправлена. Ожидайте активации."
    return {"message": msg, "user_id": str(user.id)}


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token отсутствует",
        )

    service = AuthService(db, redis)
    try:
        user, access_token, new_refresh = await service.refresh_tokens(refresh_token)
    except ValueError as e:
        _raise(str(e))

    is_secure = settings.ENVIRONMENT != "development"
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        samesite="strict",
        secure=is_secure,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenRefreshResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    refresh_token = request.cookies.get("refresh_token")

    service = AuthService(db, redis)
    await service.logout(access_token, refresh_token)

    response.delete_cookie("refresh_token", path="/api/v1/auth")


@router.get("/me", response_model=UserBrief)
async def me(current_user: User = Depends(get_current_user)):
    return UserBrief.model_validate(current_user)
