# src/findex/web/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    index_path: Path = Path("index.json")
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    model_config = SettingsConfigDict(env_prefix="FINDEX_", env_file=".env", extra="ignore")


settings = Settings()