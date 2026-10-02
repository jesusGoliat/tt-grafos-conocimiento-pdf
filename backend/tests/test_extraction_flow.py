"""Flujo completo subida → MinerU (simulado con respx) → resultado."""
import httpx
import respx

from app.services.extraction import compute_stats, unpack_mineru_zip
from tests.conftest import MINERU, UPLOAD_URL, ZIP_URL, make_mineru_zip


def mock_mineru(states: list[dict], zip_bytes: bytes | None = None):
    respx.post(f"{MINERU}/file-urls/batch").respond(
        json={"code": 0, "msg": "ok", "data": {"batch_id": "b1", "file_urls": [UPLOAD_URL]}}
    )
    respx.put(UPLOAD_URL).respond(200)
    respx.get(f"{MINERU}/extract-results/batch/b1").mock(
        side_effect=[
            httpx.Response(200, json={"code": 0, "msg": "ok", "data": {"batch_id": "b1", "extract_result": [s]}})
            for s in states
        ]
    )
    respx.get(ZIP_URL).respond(200, content=zip_bytes or make_mineru_zip())


def upload(client, data, name="doc.pdf"):
    return client.post("/api/documents", files={"file": (name, data, "application/pdf")})


@respx.mock
def test_full_flow(client, pdf_bytes):
    mock_mineru(
        [
            {"state": "pending"},
            {"state": "running", "extract_progress": {"extracted_pages": 1, "total_pages": 2}},
            {"state": "done", "full_zip_url": ZIP_URL},
        ]
    )
    response = upload(client, pdf_bytes)
    assert response.status_code == 202
    doc = response.json()
    assert doc["status"] == "queued" and doc["pages"] == 2

    # TestClient ejecuta las BackgroundTasks antes de devolver la respuesta.
    status = client.get(f"/api/documents/{doc['id']}").json()
    assert status["status"] == "done", status
    assert status["error"] is None

    put_request = respx.calls[1].request
    assert put_request.method == "PUT" and "authorization" not in put_request.headers
    assert respx.calls[0].request.headers["authorization"] == "Bearer test-token"

    result = client.get(f"/api/documents/{doc['id']}/result").json()
    assert result["markdown"].startswith("# Objetivo general")
    assert len(result["content_list"]) == 4
    assert result["stats"]["blocks_by_type"] == {"title": 1, "text": 1, "table": 1, "image": 1}

    image = client.get(f"{result['assets_base_url']}images/fig.jpg")
    assert image.status_code == 200 and image.content.startswith(b"\xff\xd8")

    listing = client.get("/api/documents").json()
    assert [d["id"] for d in listing] == [doc["id"]]


@respx.mock
def test_mineru_reports_failure(client, pdf_bytes):
    mock_mineru([{"state": "failed", "err_msg": "file parse failed"}])
    doc = upload(client, pdf_bytes).json()
    status = client.get(f"/api/documents/{doc['id']}").json()
    assert status["status"] == "failed"
    assert "file parse failed" in status["error"]
    response = client.get(f"/api/documents/{doc['id']}/result")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "extraction_failed"


@respx.mock
def test_invalid_token(client, pdf_bytes):
    respx.post(f"{MINERU}/file-urls/batch").respond(json={"code": "A0202", "msg": "token error"})
    doc = upload(client, pdf_bytes).json()
    status = client.get(f"/api/documents/{doc['id']}").json()
    assert status["status"] == "failed"
    assert "Token de MinerU inválido" in status["error"]


@respx.mock
def test_poll_timeout(client, settings, pdf_bytes):
    settings.mineru_poll_timeout_s = 0
    mock_mineru([{"state": "running"}])
    doc = upload(client, pdf_bytes).json()
    status = client.get(f"/api/documents/{doc['id']}").json()
    assert status["status"] == "failed"
    assert "Tiempo de espera agotado" in status["error"]


def test_missing_token(client, settings, pdf_bytes):
    settings.mineru_api_token = ""
    doc = upload(client, pdf_bytes).json()
    status = client.get(f"/api/documents/{doc['id']}").json()
    assert status["status"] == "failed"
    assert "MINERU_API_TOKEN" in status["error"]


def test_unpack_zip_in_subfolder_and_blocks_zip_slip(tmp_path):
    out = tmp_path / "out"
    unpack_mineru_zip(make_mineru_zip(root="abc/"), out)
    assert (out / "document.md").read_text().startswith("# Objetivo general")
    assert (out / "content_list.json").is_file()
    assert (out / "layout.json").is_file()
    assert (out / "images" / "fig.jpg").is_file()
    assert not (tmp_path / "evil.txt").exists() and not (out / "evil.txt").exists()


def test_compute_stats():
    stats = compute_stats("# Título\n\nDos palabras", [{"type": "text", "text_level": 1}, {"type": "text"}], pages=1)
    assert stats["words"] == 3
    assert stats["blocks_by_type"] == {"title": 1, "text": 1}
