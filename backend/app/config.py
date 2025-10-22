from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    google_api_key: str
    secret_key: str
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
