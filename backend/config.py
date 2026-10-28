"""ContentGuard · Application settings loaded from environment or .env."""

from pathlib import Path
from pydantic_settings import BaseSettings


_BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # Paths
    rules_path: Path = _BACKEND_DIR / "config" / "rules.yaml"
    db_path: Path = _BACKEND_DIR / "contentguard.db"

    # Transformer model — downloaded on first start and cached
    transformer_model: str = "unitary/toxic-bert"

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: list[str] = ["*"]

    # Limits
    max_text_length: int = 2000

    model_config = {"env_prefix": "CG_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
