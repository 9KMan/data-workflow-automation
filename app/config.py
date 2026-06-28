"""Environment configuration — all settings from environment variables."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API
    API_KEY: str = "dev-api-key-change-me"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://automation:automation@localhost:5432/automation_db"

    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/test"

    # ETL
    ETL_MAX_RETRIES: int = 3
    ETL_BATCH_SIZE: int = 1000


settings = Settings()