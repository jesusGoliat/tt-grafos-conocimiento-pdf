"""Orquestación de la extracción: envía el PDF al extractor, guarda la salida normalizada y actualiza el job."""
import asyncio
import io
import json
import logging
import re
import shutil
import time
import zipfile
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings
from app.core.errors import AppError, ExtractionError
from app.models.job import JobStatus, Progress, utcnow
from app.services.mineru_client import MinerUClient
from app.services.storage import CONTENT_LIST_FILE, LAYOUT_FILE, MARKDOWN_FILE, JobStore

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[JobStatus, Progress], Awaitable[None]]


class Extractor(Protocol):
    """Interfaz común para motores de extracción (MinerU en la nube hoy; MinerU local u otro en el futuro)."""

    name: str

    async def extract(self, pdf_path: Path, filename: str, out_dir: Path, on_progress: ProgressCallback) -> None:
        """Extrae `pdf_path` y deja en `out_dir` document.md, content_list.json, layout.json e images/."""
        ...


class MinerUApiExtractor:
    name = "mineru-api"

    def __init__(self, client: MinerUClient, settings: Settings):
        self.client = client
        self.settings = settings

    async def extract(self, pdf_path: Path, filename: str, out_dir: Path, on_progress: ProgressCallback) -> None:
        await on_progress(JobStatus.UPLOADING, Progress())
        batch_id, upload_url = await self.client.request_upload_url(filename, data_id=pdf_path.stem)
        await self.client.upload_file(upload_url, pdf_path)
        logger.info("PDF %s subido a MinerU (batch %s)", pdf_path.name, batch_id)

        deadline = time.monotonic() + self.settings.mineru_poll_timeout_s
        last_seen = None
        while True:
            result = await self.client.get_batch_result(batch_id)
            seen = (result.state, result.extracted_pages)
            if seen != last_seen:
                logger.info("MinerU batch %s: %s (%s/%s páginas)", batch_id, result.state, result.extracted_pages, result.total_pages)
                last_seen = seen
            await on_progress(
                JobStatus.PROCESSING,
                Progress(
                    extracted_pages=result.extracted_pages,
                    total_pages=result.total_pages,
                    remote_state=result.state,
                ),
            )
            if result.state == "done":
                if not result.full_zip_url:
                    raise ExtractionError("MinerU terminó pero no devolvió la URL del resultado.")
                break
            if result.state == "failed":
                raise ExtractionError(f"MinerU no pudo extraer el documento: {result.err_msg or 'sin detalle'}")
            if time.monotonic() > deadline:
                raise ExtractionError(
                    f"Tiempo de espera agotado ({self.settings.mineru_poll_timeout_s:.0f} s) esperando a MinerU.",
                    code="mineru_timeout",
                )
            await asyncio.sleep(self.settings.mineru_poll_interval_s)

        archive = await self.client.download(result.full_zip_url)
        unpack_mineru_zip(archive, out_dir)


def _find(names: list[str], predicate: Callable[[str], bool]) -> str | None:
    matches = sorted((n for n in names if predicate(n)), key=len)
    return matches[0] if matches else None


def unpack_mineru_zip(archive: bytes, out_dir: Path) -> None:
    """Descomprime el ZIP de MinerU en `out_dir` con nombres normalizados."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(archive))
    except zipfile.BadZipFile as exc:
        raise ExtractionError("El resultado de MinerU no es un ZIP válido.") from exc

    with zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        md_name = _find(names, lambda n: Path(n).name == "full.md") or _find(names, lambda n: n.endswith(".md"))
        if not md_name:
            raise ExtractionError("El resultado de MinerU no contiene Markdown.")
        root = str(Path(md_name).parent) + "/" if "/" in md_name else ""
        content_name = _find(names, lambda n: n.endswith("content_list.json"))
        layout_name = _find(names, lambda n: Path(n).name in ("layout.json", "middle.json") or n.endswith("_middle.json"))

        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MARKDOWN_FILE).write_bytes(zf.read(md_name))
        (out_dir / CONTENT_LIST_FILE).write_bytes(zf.read(content_name) if content_name else b"[]")
        if layout_name:
            (out_dir / LAYOUT_FILE).write_bytes(zf.read(layout_name))

        images_dir = out_dir / "images"
        if images_dir.exists():
            shutil.rmtree(images_dir)
        images_root = (images_dir).resolve()
        prefix = f"{root}images/"
        for name in names:
            if not name.startswith(prefix):
                continue
            target = (images_dir / name[len(prefix):]).resolve()
            if not target.is_relative_to(images_root):  # protección contra "zip slip"
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(name))


def block_type(block: dict[str, Any]) -> str:
    kind = block.get("type", "unknown")
    if kind == "text" and block.get("text_level"):
        return "title"
    return kind


def compute_stats(markdown: str, content_list: list[dict[str, Any]], pages: int) -> dict[str, Any]:
    by_type = Counter(block_type(b) for b in content_list)
    plain = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)|[#*_`|>-]", " ", markdown)
    return {
        "pages": pages,
        "blocks_total": len(content_list),
        "blocks_by_type": dict(by_type.most_common()),
        "characters": len(re.sub(r"\s+", "", plain)),
        "words": len(plain.split()),
    }


def load_result(out_dir: Path) -> tuple[str, list[dict[str, Any]]]:
    markdown = (out_dir / MARKDOWN_FILE).read_text(encoding="utf-8")
    content_path = out_dir / CONTENT_LIST_FILE
    content_list = json.loads(content_path.read_text(encoding="utf-8")) if content_path.is_file() else []
    return markdown, content_list if isinstance(content_list, list) else []


async def run_extraction(job_id: str, store: JobStore, extractor: Extractor) -> None:
    """Tarea en segundo plano: ejecuta la extracción y refleja cada cambio de estado en el job."""
    job = store.get(job_id)
    if job is None:
        return

    async def on_progress(status: JobStatus, progress: Progress) -> None:
        job.status = status
        job.progress = progress
        store.save(job)

    try:
        await extractor.extract(store.pdf_path(job_id), job.filename, store.result_dir(job_id), on_progress)
        job.status = JobStatus.DONE
        job.error = None
    except AppError as exc:
        logger.warning("Extracción %s falló: %s", job_id, exc.message)
        job.status, job.error = JobStatus.FAILED, exc.message
    except Exception as exc:  # cualquier fallo inesperado se refleja en el job en lugar de perderse
        logger.exception("Error inesperado en la extracción %s", job_id)
        job.status, job.error = JobStatus.FAILED, f"Error inesperado: {exc}"
    job.finished_at = utcnow()
    store.save(job)
