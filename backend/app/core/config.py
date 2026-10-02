"""Configuración de la aplicación, leída de variables de entorno o de `backend/.env`."""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PDF Knowledge Graph - Prototipo 1"
    data_dir: Path = BACKEND_DIR / "data"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Validación de archivos
    max_upload_mb: int = 50
    max_pages: int = 200  # límite de la API de MinerU

    # API de MinerU (https://mineru.net/apiManage/docs)
    mineru_api_token: str = ""
    mineru_base_url: str = "https://mineru.net/api/v4"
    mineru_model_version: Literal["pipeline", "vlm"] = "pipeline"
    # Códigos de OCR de MinerU; el español pertenece a la familia "latin" ("es" no es válido).
    mineru_language: Literal[
        "ch", "ch_server", "en", "japan", "korean", "chinese_cht", "ta", "te", "ka", "el", "th",
        "latin", "arabic", "cyrillic", "east_slavic", "devanagari",
    ] = "latin"
    mineru_enable_table: bool = True
    mineru_enable_formula: bool = True
    mineru_is_ocr: bool = False
    mineru_poll_interval_s: float = 3.0
    mineru_poll_timeout_s: float = 900.0
    mineru_http_timeout_s: float = 60.0

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
