"""Cliente de la API de precisión de MinerU (v4).

Flujo para archivos locales (https://mineru.net/apiManage/docs):
    1. POST /file-urls/batch            -> batch_id + URL prefirmada de subida
    2. PUT  <URL prefirmada>            -> sube el PDF; MinerU encola la extracción automáticamente
    3. GET  /extract-results/batch/{id} -> estado (waiting-file, pending, running, converting, done, failed)
    4. GET  full_zip_url                -> ZIP con full.md, *_content_list.json, layout.json, images/
"""
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import Settings
from app.core.errors import ExtractionError

ERROR_MESSAGES = {
    "A0202": "Token de MinerU inválido. Revisa MINERU_API_TOKEN.",
    "A0211": "El token de MinerU expiró. Genera uno nuevo en mineru.net.",
    "-500": "Parámetros inválidos enviados a MinerU.",
    "-10001": "Error interno del servicio de MinerU.",
    "-10002": "Parámetros de solicitud inválidos.",
    "-60001": "MinerU no pudo generar la URL de subida.",
    "-60002": "MinerU no reconoció el formato del archivo.",
    "-60003": "MinerU no pudo leer el archivo.",
    "-60004": "El archivo está vacío.",
    "-60005": "El archivo excede el tamaño máximo de MinerU.",
    "-60006": "El archivo excede el número máximo de páginas de MinerU.",
    "-60007": "El servicio de modelos de MinerU no está disponible.",
    "-60008": "Tiempo de lectura del archivo agotado en MinerU.",
    "-60009": "La cola de tareas de MinerU está llena; intenta más tarde.",
    "-60010": "MinerU no pudo procesar el documento.",
    "-60012": "MinerU no encontró la tarea.",
    "-60013": "Sin permiso para acceder a la tarea en MinerU.",
}


@dataclass
class BatchFileResult:
    state: str
    err_msg: str = ""
    full_zip_url: str | None = None
    extracted_pages: int | None = None
    total_pages: int | None = None


class MinerUClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None):
        self.settings = settings
        self._http = http or httpx.AsyncClient(timeout=settings.mineru_http_timeout_s)

    async def aclose(self) -> None:
        await self._http.aclose()

    @property
    def _headers(self) -> dict[str, str]:
        if not self.settings.mineru_api_token:
            raise ExtractionError(
                "No hay token de MinerU configurado. Define MINERU_API_TOKEN en backend/.env.",
                code="mineru_token_missing",
            )
        return {"Authorization": f"Bearer {self.settings.mineru_api_token}", "Content-Type": "application/json"}

    def _unwrap(self, response: httpx.Response) -> dict:
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.status_code in (401, 403):
            raise ExtractionError(ERROR_MESSAGES["A0202"], code="mineru_auth")
        if not isinstance(body, dict):
            raise ExtractionError(f"Respuesta inesperada de MinerU (HTTP {response.status_code}).", code="mineru_http")
        code = str(body.get("code"))
        if code != "0":
            message = ERROR_MESSAGES.get(code) or body.get("msg") or "Error desconocido"
            raise ExtractionError(f"MinerU [{code}]: {message}", code="mineru_api")
        return body.get("data") or {}

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = await self._http.request(
                method, f"{self.settings.mineru_base_url}{path}", headers=self._headers, **kwargs
            )
        except httpx.HTTPError as exc:
            raise ExtractionError(f"No se pudo contactar a MinerU: {exc}", code="mineru_unreachable") from exc
        return self._unwrap(response)

    async def request_upload_url(self, filename: str, data_id: str) -> tuple[str, str]:
        payload = {
            "files": [{"name": filename, "data_id": data_id, "is_ocr": self.settings.mineru_is_ocr}],
            "model_version": self.settings.mineru_model_version,
            "language": self.settings.mineru_language,
            "enable_table": self.settings.mineru_enable_table,
            "enable_formula": self.settings.mineru_enable_formula,
        }
        data = await self._request("POST", "/file-urls/batch", json=payload)
        try:
            return data["batch_id"], data["file_urls"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExtractionError("MinerU no devolvió batch_id o URL de subida.", code="mineru_api") from exc

    async def upload_file(self, upload_url: str, pdf_path: Path) -> None:
        # La URL prefirmada no acepta cabecera Content-Type ni Authorization.
        try:
            response = await self._http.put(upload_url, content=pdf_path.read_bytes())
        except httpx.HTTPError as exc:
            raise ExtractionError(f"Falló la subida del PDF a MinerU: {exc}", code="mineru_upload") from exc
        if response.status_code >= 400:
            raise ExtractionError(f"Falló la subida del PDF a MinerU (HTTP {response.status_code}).", code="mineru_upload")

    async def get_batch_result(self, batch_id: str) -> BatchFileResult:
        data = await self._request("GET", f"/extract-results/batch/{batch_id}")
        results = data.get("extract_result") or []
        if not results:
            # Justo después de subir, MinerU puede no listar todavía el archivo.
            return BatchFileResult(state="waiting-file")
        item = results[0]
        progress = item.get("extract_progress") or {}
        return BatchFileResult(
            state=item.get("state", "pending"),
            err_msg=item.get("err_msg") or "",
            full_zip_url=item.get("full_zip_url") or None,
            extracted_pages=progress.get("extracted_pages"),
            total_pages=progress.get("total_pages"),
        )

    async def download(self, url: str) -> bytes:
        try:
            response = await self._http.get(url, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExtractionError(f"No se pudo descargar el resultado de MinerU: {exc}", code="mineru_download") from exc
        return response.content
