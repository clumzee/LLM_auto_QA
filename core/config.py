from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

class DevelopmentSettings(Settings):
    class Config:
        env_file = ".env"


def get_settings():
    import os
    env = os.getenv("ENV", "dev")
    return DevelopmentSettings()

settings = get_settings()
