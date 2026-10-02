import io
import json
import zipfile
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

SAMPLE_PDF = Path(__file__).resolve().parents[2] / "samples" / "2027-A038.pdf"
MINERU = "https://mineru.test/api/v4"
UPLOAD_URL = "https://upload.mineru.test/api-upload/abc"
ZIP_URL = "https://cdn.mineru.test/result.zip"


def make_pdf(pages: int = 1, text: str = "Hola mundo", password: str | None = None) -> bytes:
    doc = pymupdf.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"{text} {i + 1}")
    kwargs = {}
    if password:
        kwargs = dict(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
    data = doc.tobytes(**kwargs)
    doc.close()
    return data


def make_mineru_zip(*, root: str = "") -> bytes:
    """ZIP con la misma forma que devuelve MinerU."""
    content_list = [
        {"type": "text", "text": "Objetivo general", "text_level": 1, "page_idx": 0},
        {"type": "text", "text": "Desarrollar un sistema...", "page_idx": 0},
        {"type": "table", "table_body": "<table><tr><td>A</td></tr></table>", "page_idx": 1},
        {"type": "image", "img_path": "images/fig.jpg", "page_idx": 1},
    ]
    markdown = "# Objetivo general\n\nDesarrollar un sistema...\n\n<table><tr><td>A</td></tr></table>\n\n![](images/fig.jpg)\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{root}full.md", markdown)
        zf.writestr(f"{root}abc_content_list.json", json.dumps(content_list))
        zf.writestr(f"{root}layout.json", json.dumps({"pdf_info": []}))
        zf.writestr(f"{root}abc_model.json", "[]")
        zf.writestr(f"{root}images/fig.jpg", b"\xff\xd8fake-jpeg")
        zf.writestr(f"{root}images/../../evil.txt", b"zip slip")
    return buf.getvalue()


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        mineru_api_token="test-token",
        mineru_base_url=MINERU,
        mineru_poll_interval_s=0,
        mineru_poll_timeout_s=5,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def pdf_bytes() -> bytes:
    return make_pdf(pages=2)
