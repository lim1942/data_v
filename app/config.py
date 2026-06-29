from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data.db"


class Settings(BaseSettings):
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    model_config = {"env_file": ".env"}


settings = Settings()
