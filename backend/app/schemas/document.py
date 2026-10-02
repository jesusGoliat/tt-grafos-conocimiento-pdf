"""Esquemas de respuesta de la API de documentos."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.job import JobStatus, Progress


class DocumentStatus(BaseModel):
    id: str
    filename: str
    size_bytes: int
    pages: int
    status: JobStatus
    progress: Progress
    error: str | None
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None


class ExtractionStats(BaseModel):
    pages: int
    blocks_total: int
    blocks_by_type: dict[str, int]
    characters: int
    words: int


class ExtractionResult(BaseModel):
    id: str
    filename: str
    markdown: str
    content_list: list[dict[str, Any]]
    stats: ExtractionStats
    assets_base_url: str


class HealthStatus(BaseModel):
    status: str
    mineru_token_configured: bool
    mineru_model_version: str
