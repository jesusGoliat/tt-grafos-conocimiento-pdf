"""Almacenamiento en disco de PDFs, resultados y metadatos de los jobs.

Estructura:
    data/uploads/{id}.pdf
    data/results/{id}/metadata.json      estado del job
    data/results/{id}/document.md        Markdown extraído
    data/results/{id}/content_list.json  bloques estructurados (tipo, página, nivel de título...)
    data/results/{id}/layout.json        layout detallado de MinerU
    data/results/{id}/images/            imágenes y tablas recortadas
"""
import threading
from pathlib import Path

from app.models.job import Job, utcnow

MARKDOWN_FILE = "document.md"
CONTENT_LIST_FILE = "content_list.json"
LAYOUT_FILE = "layout.json"
METADATA_FILE = "metadata.json"


class JobStore:
    def __init__(self, uploads_dir: Path, results_dir: Path):
        self.uploads_dir = uploads_dir
        self.results_dir = results_dir
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def pdf_path(self, job_id: str) -> Path:
        return self.uploads_dir / f"{job_id}.pdf"

    def result_dir(self, job_id: str) -> Path:
        return self.results_dir / job_id

    def save_pdf(self, job_id: str, data: bytes) -> Path:
        path = self.pdf_path(job_id)
        path.write_bytes(data)
        return path

    def save(self, job: Job) -> Job:
        job.updated_at = utcnow()
        directory = self.result_dir(job.id)
        directory.mkdir(parents=True, exist_ok=True)
        tmp = directory / f"{METADATA_FILE}.tmp"
        with self._lock:
            tmp.write_text(job.model_dump_json(indent=2), encoding="utf-8")
            tmp.replace(directory / METADATA_FILE)  # escritura atómica
        return job

    def get(self, job_id: str) -> Job | None:
        path = self.result_dir(job_id) / METADATA_FILE
        # Los ids son uuid4 hex; esto evita rutas arbitrarias.
        if not job_id.isalnum() or not path.is_file():
            return None
        with self._lock:
            return Job.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[Job]:
        jobs = [job for d in self.results_dir.iterdir() if d.is_dir() and (job := self.get(d.name))]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
