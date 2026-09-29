from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "JobAIgent"
    APP_ENV: str = "development"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database
    DATABASE_URL: str
    SYNC_DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "jobaigent-resumes"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_BASIC: str = ""   # $3.99
    STRIPE_PRICE_ID_PRO: str = ""     # $7.99

    # Job board credentials
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""
    INDEED_EMAIL: str = ""
    INDEED_PASSWORD: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@jobaigent.com"

    # Plan limits
    PLAN_FREE_DAILY_LIMIT: int = 12       # 10-15 → use 12 as default
    PLAN_BASIC_DAILY_LIMIT: int = 22      # 20-25 → use 22
    PLAN_PRO_DAILY_LIMIT: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
