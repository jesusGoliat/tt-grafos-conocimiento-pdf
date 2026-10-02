"""Punto de entrada de la API (FastAPI)."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.models.job import JobStatus, utcnow
from app.schemas.document import HealthStatus
from app.services.extraction import Extractor, MinerUApiExtractor
from app.services.mineru_client import MinerUClient
from app.services.storage import JobStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _fail_interrupted_jobs(store: JobStore) -> None:
    """Los jobs que quedaron a medias por un reinicio del servidor se marcan como fallidos."""
    for job in store.list():
        if job.status not in (JobStatus.DONE, JobStatus.FAILED):
            job.status = JobStatus.FAILED
            job.error = "La extracción se interrumpió porque el servidor se reinició. Vuelve a subir el archivo."
            job.finished_at = utcnow()
            store.save(job)


def create_app(settings: Settings | None = None, extractor: Extractor | None = None) -> FastAPI:
    settings = settings or get_settings()
    store = JobStore(settings.uploads_dir, settings.results_dir)
    client: MinerUClient | None = None
    if extractor is None:
        client = MinerUClient(settings)
        extractor = MinerUApiExtractor(client, settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _fail_interrupted_jobs(store)
        yield
        if client:
            await client.aclose()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.store = store
    app.state.extractor = extractor

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(documents.router)

    @app.get("/api/health", response_model=HealthStatus, tags=["health"])
    async def health():
        return HealthStatus(
            status="ok",
            mineru_token_configured=bool(settings.mineru_api_token),
            mineru_model_version=settings.mineru_model_version,
        )

    return app


app = create_app()
