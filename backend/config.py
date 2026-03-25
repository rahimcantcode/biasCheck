import os
from functools import lru_cache
from pathlib import Path
from typing import List


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DEFAULT_MODEL_DIR = REPO_ROOT / "bias_model"


class Settings:
    def __init__(self) -> None:
        self.environment = os.getenv("BIASCHECK_ENV", "development")
        self.model_dir = Path(os.getenv("BIASCHECK_MODEL_DIR", str(DEFAULT_MODEL_DIR))).expanduser().resolve()
        self.allowed_origins = self._parse_origins(
            os.getenv(
                "BIASCHECK_ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        )
        self.backend_host = os.getenv("BIASCHECK_BACKEND_HOST", "127.0.0.1")
        self.backend_port = int(os.getenv("BIASCHECK_BACKEND_PORT", "8000"))
        self.request_timeout = int(os.getenv("BIASCHECK_REQUEST_TIMEOUT", "10"))

    @staticmethod
    def _parse_origins(raw_origins: str) -> List[str]:
        if not raw_origins.strip():
            return []
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
