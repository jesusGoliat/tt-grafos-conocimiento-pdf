"""Prueba contra la API real de MinerU con el PDF de ejemplo.

Ejecutar con:  pytest -m integration
Requiere MINERU_API_TOKEN en backend/.env (si no existe, la prueba se omite).
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.conftest import SAMPLE_PDF

pytestmark = pytest.mark.integration


def test_extract_sample_pdf_with_real_mineru(tmp_path):
    settings = Settings(data_dir=tmp_path / "data")
    if not settings.mineru_api_token:
        pytest.skip("MINERU_API_TOKEN no configurado")

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/documents", files={"file": (SAMPLE_PDF.name, SAMPLE_PDF.read_bytes(), "application/pdf")}
        )
        assert response.status_code == 202, response.text
        doc_id = response.json()["id"]

        status = client.get(f"/api/documents/{doc_id}").json()
        assert status["status"] == "done", status

        result = client.get(f"/api/documents/{doc_id}/result").json()
    markdown = result["markdown"]
    assert "Objetivo general" in markdown
    assert "Grafos de Conocimiento" in markdown or "grafos de conocimiento" in markdown
    assert "<table" in markdown or "|" in markdown  # Tabla 1 del protocolo
    assert result["stats"]["blocks_by_type"].get("table", 0) >= 1
    (tmp_path / "sample_output.md").write_text(markdown, encoding="utf-8")
