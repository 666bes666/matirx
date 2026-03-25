from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://matrix:matrix_dev@db:5432/matrix"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = "change-me-in-production-use-at-least-64-characters-here-please"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BCRYPT_ROUNDS: int = 12

    TELEGRAM_BOT_TOKEN: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
