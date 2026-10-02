"""Modelo del job de extracción, persistido como metadata.json por documento."""
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"          # recibido y validado, aún no se envía a MinerU
    UPLOADING = "uploading"    # subiendo el PDF a MinerU
    PROCESSING = "processing"  # MinerU está extrayendo
    DONE = "done"
    FAILED = "failed"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Progress(BaseModel):
    extracted_pages: int | None = None
    total_pages: int | None = None
    remote_state: str | None = None  # estado reportado por MinerU (pending, running, converting...)


class Job(BaseModel):
    id: str
    filename: str
    size_bytes: int
    pages: int
    status: JobStatus = JobStatus.QUEUED
    progress: Progress = Field(default_factory=Progress)
    error: str | None = None
    engine: str = "mineru-api"
    remote_batch_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
