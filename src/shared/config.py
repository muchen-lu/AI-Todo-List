import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CURRENT_ENV = os.getenv("ENVIRONMENT", "development")
PREFIX: str = "demo_" if CURRENT_ENV == "development" else ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_prefix=PREFIX)

    gemini_api_key: str = Field(validation_alias="GEMINI_API_KEY", description="Gemini API Key")
    database_url: str = Field(validation_alias="DATABASE_URL", description="Project Database URL")
    database_key: str = Field(validation_alias="FIREBASE_KEY", description="Firebase Key")

    ono_username: str = Field(validation_alias="ONO_USERNAME", description="ONO username")
    ono_password: str = Field(validation_alias="ONO_PASSWORD", description="ONO password")

    line_channel_access_token: str = Field(description="Line Channel Access Token")
    line_channel_secret: str = Field(description="Line Channel Secret")
    # line_user_id: str = Field(description="Line User ID")


@lru_cache
def get_settings():
    return Settings()
