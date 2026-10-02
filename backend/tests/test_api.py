"""Endpoints: validación de entrada, códigos de error y protección de rutas."""
from app.models.job import Job, JobStatus
from app.services.storage import JobStore


def test_health(client):
    body = client.get("/api/health").json()
    assert body == {"status": "ok", "mineru_token_configured": True, "mineru_model_version": "pipeline"}


def test_upload_rejects_non_pdf(client):
    response = client.post("/api/documents", files={"file": ("notas.txt", b"hola", "text/plain")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_file"


def test_upload_rejects_too_large(client, settings, pdf_bytes):
    settings.max_upload_mb = 0
    response = client.post("/api/documents", files={"file": ("doc.pdf", pdf_bytes, "application/pdf")})
    assert response.status_code == 413


def test_upload_without_file(client):
    response = client.post("/api/documents")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation"


def test_unknown_document(client):
    assert client.get("/api/documents/noexiste").status_code == 404
    assert client.get("/api/documents/noexiste/result").status_code == 404
    assert client.get("/api/documents/../../etc/passwd").status_code == 404


def test_result_not_ready(client):
    store: JobStore = client.app.state.store
    store.save(Job(id="abc123", filename="a.pdf", size_bytes=1, pages=1, status=JobStatus.PROCESSING))
    response = client.get("/api/documents/abc123/result")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_ready"


def test_asset_path_traversal(client):
    store: JobStore = client.app.state.store
    store.save(Job(id="abc123", filename="a.pdf", size_bytes=1, pages=1, status=JobStatus.DONE))
    for path in ["metadata.json", "images/../metadata.json", "images/%2e%2e/metadata.json"]:
        assert client.get(f"/api/documents/abc123/assets/{path}").status_code == 404


def test_interrupted_jobs_marked_failed(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    store = JobStore(settings.uploads_dir, settings.results_dir)
    store.save(Job(id="abc123", filename="a.pdf", size_bytes=1, pages=1, status=JobStatus.PROCESSING))
    with TestClient(create_app(settings)) as c:
        body = c.get("/api/documents/abc123").json()
    assert body["status"] == "failed" and "reinició" in body["error"]
