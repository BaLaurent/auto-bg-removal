from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_dir: Path = Path("/app/checkpoints")
    lru_size: int = 8
    predictor_backend: str = "fake"  # "fake" | "sam2"
    default_model: str = "sam2_hiera_base_plus"


def get_settings() -> Settings:
    return Settings()
