import pytest

from app.core.errors import FileTooLargeError, InvalidFileError
from app.services.validation import validate_pdf
from tests.conftest import SAMPLE_PDF, make_pdf

MB = 1024 * 1024


def check(data, filename="doc.pdf", content_type="application/pdf", max_bytes=10 * MB, max_pages=200):
    return validate_pdf(data, filename, content_type, max_bytes=max_bytes, max_pages=max_pages)


def test_valid_generated_pdf():
    info = check(make_pdf(pages=3))
    assert info.pages == 3


def test_valid_sample_pdf():
    info = check(SAMPLE_PDF.read_bytes(), filename=SAMPLE_PDF.name)
    assert info.pages == 9


@pytest.mark.parametrize(
    "data, filename, content_type, error",
    [
        (b"%PDF-1.7 ...", "doc.txt", "application/pdf", "extensión"),
        (b"%PDF-1.7 ...", "doc.pdf", "image/png", "Tipo de contenido"),
        (b"", "doc.pdf", "application/pdf", "vacío"),
        (b"hola, no soy un pdf", "doc.pdf", "application/pdf", "firma"),
        (b"%PDF-1.7\nbasura sin estructura", "doc.pdf", "application/pdf", "dañado"),
    ],
)
def test_invalid_files(data, filename, content_type, error):
    with pytest.raises(InvalidFileError, match=error):
        check(data, filename, content_type)


def test_too_large():
    with pytest.raises(FileTooLargeError):
        check(make_pdf(), max_bytes=10)


def test_too_many_pages():
    with pytest.raises(InvalidFileError, match="páginas"):
        check(make_pdf(pages=3), max_pages=2)


def test_encrypted_pdf():
    with pytest.raises(InvalidFileError, match="contraseña"):
        check(make_pdf(password="secreto"))
