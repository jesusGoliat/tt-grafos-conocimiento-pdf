"""Validación de los PDF recibidos antes de enviarlos a extracción."""
from dataclasses import dataclass

import pymupdf

from app.core.errors import FileTooLargeError, InvalidFileError

PDF_MAGIC = b"%PDF-"
ACCEPTED_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream", ""}


@dataclass(frozen=True)
class PdfInfo:
    pages: int
    size_bytes: int


def validate_pdf(
    data: bytes,
    filename: str | None,
    content_type: str | None,
    *,
    max_bytes: int,
    max_pages: int,
) -> PdfInfo:
    """Verifica nombre, tipo, tamaño, firma y que el PDF se pueda abrir. Lanza AppError si no es válido."""
    if not filename or not filename.lower().endswith(".pdf"):
        raise InvalidFileError("El archivo debe tener extensión .pdf.")
    if (content_type or "") not in ACCEPTED_CONTENT_TYPES:
        raise InvalidFileError(f"Tipo de contenido no soportado: {content_type}. Se esperaba application/pdf.")
    if not data:
        raise InvalidFileError("El archivo está vacío.")
    if len(data) > max_bytes:
        raise FileTooLargeError(f"El archivo excede el tamaño máximo de {max_bytes // (1024 * 1024)} MB.")
    if not data.startswith(PDF_MAGIC):
        raise InvalidFileError("El contenido no corresponde a un PDF (firma %PDF- ausente).")

    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise InvalidFileError("El PDF está protegido con contraseña.")
            pages = doc.page_count
    except InvalidFileError:
        raise
    except Exception as exc:  # PyMuPDF lanza distintos tipos según el daño del archivo
        raise InvalidFileError(f"El PDF está dañado o no se puede leer: {exc}") from exc

    if pages == 0:
        raise InvalidFileError("El PDF no contiene páginas.")
    if pages > max_pages:
        raise InvalidFileError(f"El PDF tiene {pages} páginas; el máximo permitido es {max_pages}.")
    return PdfInfo(pages=pages, size_bytes=len(data))
