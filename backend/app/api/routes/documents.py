"""Rutas REST para subir PDFs y consultar su extracción."""
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.core.errors import FileTooLargeError, NotFoundError, NotReadyError
from app.models.job import Job, JobStatus
from app.schemas.document import DocumentStatus, ExtractionResult, ExtractionStats
from app.services.extraction import compute_stats, load_result, run_extraction
from app.services.storage import JobStore
from app.services.validation import validate_pdf

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _store(request: Request) -> JobStore:
    return request.app.state.store


def _get_job(request: Request, job_id: str) -> Job:
    job = _store(request).get(job_id)
    if job is None:
        raise NotFoundError(f"No existe el documento {job_id}.")
    return job


def _to_status(job: Job) -> DocumentStatus:
    return DocumentStatus.model_validate(job.model_dump())


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentStatus)
async def upload_document(request: Request, background: BackgroundTasks, file: UploadFile = File(...)):
    """Recibe un PDF, lo valida y lanza su extracción en segundo plano."""
    settings = request.app.state.settings
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise FileTooLargeError(f"El archivo excede el tamaño máximo de {settings.max_upload_mb} MB.")
    info = validate_pdf(
        data,
        file.filename,
        file.content_type,
        max_bytes=settings.max_upload_bytes,
        max_pages=settings.max_pages,
    )

    store = _store(request)
    job = Job(
        id=uuid.uuid4().hex,
        filename=file.filename,
        size_bytes=info.size_bytes,
        pages=info.pages,
        engine=request.app.state.extractor.name,
    )
    store.save_pdf(job.id, data)
    store.save(job)
    background.add_task(run_extraction, job.id, store, request.app.state.extractor)
    return _to_status(job)


@router.get("", response_model=list[DocumentStatus])
async def list_documents(request: Request):
    return [_to_status(job) for job in _store(request).list()]


@router.get("/{job_id}", response_model=DocumentStatus)
async def get_document(request: Request, job_id: str):
    return _to_status(_get_job(request, job_id))


@router.get("/{job_id}/result", response_model=ExtractionResult)
async def get_result(request: Request, job_id: str):
    job = _get_job(request, job_id)
    if job.status == JobStatus.FAILED:
        raise NotReadyError(f"La extracción falló: {job.error}", code="extraction_failed")
    if job.status != JobStatus.DONE:
        raise NotReadyError(f"La extracción aún no termina (estado: {job.status}).")
    markdown, content_list = load_result(_store(request).result_dir(job_id))
    return ExtractionResult(
        id=job.id,
        filename=job.filename,
        markdown=markdown,
        content_list=content_list,
        stats=ExtractionStats(**compute_stats(markdown, content_list, job.pages)),
        assets_base_url=f"/api/documents/{job.id}/assets/",
    )


@router.get("/{job_id}/assets/{asset_path:path}")
async def get_asset(request: Request, job_id: str, asset_path: str):
    """Sirve las imágenes extraídas (las referencias del Markdown son relativas: images/xxx.jpg)."""
    _get_job(request, job_id)
    base = _store(request).result_dir(job_id).resolve()
    target = (base / asset_path).resolve()
    if not target.is_relative_to(base / "images") or not target.is_file():
        raise NotFoundError("Recurso no encontrado.")
    return FileResponse(target)
