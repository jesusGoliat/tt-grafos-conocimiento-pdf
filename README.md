# Grafos de Conocimiento a partir de PDF: Prototipo 1

Aplicación web para subir un PDF y obtener su contenido extraído y estructurado (Markdown + JSON) con [MinerU](https://mineru.net). Es el primer prototipo evolutivo del Trabajo Terminal *"Generación de Grafos de Conocimiento a partir de Documentos en Formato PDF mediante LLM y NLP"*.

- **Backend:** Python 3.12 + FastAPI (`backend/`)
- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Extracción:** API en la nube de MinerU (v4)
- **Documentación:** `docs/`

## Requisitos

- Python 3.11 o superior (probado con 3.12) y el entorno virtual `~/venvs/pipeline`
- Node.js 20 o superior (probado con 24) y npm
- Un **token de la API de MinerU**: inicia sesión en https://mineru.net, entra a **API Management** y crea un token. Límites del servicio: ≤200 MB y ≤200 páginas por archivo, 1000 páginas al día con prioridad.

## Instalación

```bash
# Backend
source ~/venvs/pipeline/bin/activate
cd backend
pip install -r requirements.txt
cp .env.example .env          # edita .env y pega tu token en MINERU_API_TOKEN=

# Frontend
cd ../frontend
npm install
```

## Ejecución

Usa dos terminales.

```bash
# Terminal 1: API en http://localhost:8001 (Swagger en http://localhost:8001/docs)
source ~/venvs/pipeline/bin/activate
cd backend
uvicorn app.main:app --port 8001 --reload
```

```bash
# Terminal 2: interfaz web en http://localhost:5173
cd frontend
npm run dev
```

Abre http://localhost:5173, arrastra un PDF (por ejemplo `samples/2027-A038.pdf`) y pulsa **Extraer contenido**. La interfaz muestra el avance (subida → envío a MinerU → extracción página por página → listo) y después el resultado en cuatro pestañas: vista renderizada, Markdown, JSON estructurado y estadísticas. Ambos formatos se pueden descargar.

> El servidor de Vite redirige `/api` a `http://localhost:8001`. Si el backend corre en otro puerto, usa `BACKEND_URL=http://localhost:XXXX npm run dev`.

## Configuración (`backend/.env`)

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `MINERU_API_TOKEN` | (vacío) | Token de la API de MinerU (**obligatorio**) |
| `MINERU_MODEL_VERSION` | `pipeline` | `pipeline` o `vlm` (más preciso y más lento) |
| `MINERU_LANGUAGE` | `latin` | Familia de idioma para el OCR (`latin` cubre español; `es` no es válido) |
| `MINERU_ENABLE_TABLE` / `MINERU_ENABLE_FORMULA` | `true` | Reconocimiento de tablas y fórmulas |
| `MINERU_IS_OCR` | `false` | Forzar OCR (para PDFs escaneados) |
| `MINERU_POLL_INTERVAL_S` / `MINERU_POLL_TIMEOUT_S` | `3` / `900` | Intervalo y tiempo máximo de espera de la extracción |
| `MAX_UPLOAD_MB` | `50` | Tamaño máximo del archivo |
| `DATA_DIR` | `backend/data` | Dónde se guardan PDFs y resultados |

## API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/documents` | Sube un PDF (`multipart/form-data`, campo `file`). Responde `202` y la extracción continúa en segundo plano |
| `GET` | `/api/documents` | Lista los documentos |
| `GET` | `/api/documents/{id}` | Estado: `queued`, `uploading`, `processing`, `done`, `failed`, con avance y error |
| `GET` | `/api/documents/{id}/result` | `markdown`, `content_list` (JSON) y `stats`. Responde `409` si aún no termina |
| `GET` | `/api/documents/{id}/assets/images/...` | Imágenes extraídas |
| `GET` | `/api/health` | Estado del servicio y si hay token configurado |

Los errores siguen siempre el formato `{"error": {"code": "...", "message": "..."}}`.

Ejemplo con curl:

```bash
curl -F "file=@samples/2027-A038.pdf;type=application/pdf" http://localhost:8001/api/documents
curl http://localhost:8001/api/documents/<id>
curl http://localhost:8001/api/documents/<id>/result
```

Resultados en disco: `backend/data/results/<id>/` contiene `document.md`, `content_list.json`, `layout.json`, `images/` y `metadata.json`.

## Pruebas

```bash
source ~/venvs/pipeline/bin/activate
cd backend
pytest                  # pruebas unitarias (MinerU simulado; no requieren red ni token)
pytest -m integration   # extracción real de samples/2027-A038.pdf con MinerU (requiere token)
```

Frontend: `cd frontend && npm run build` (verifica tipos y compila).

### Fidelidad del texto (CER, objetivo 2.1.1)

```bash
cd backend
# contra una transcripción manual de una página (evaluación formal)
python scripts/eval_cer.py data/results/<id> --page 1 --ref referencia_p1.txt
# contra la capa de texto del PDF (referencia aproximada para PDFs digitales)
python scripts/eval_cer.py data/results/<id> --page 1 --ref-from-pdf data/uploads/<id>.pdf
```

## Estructura

```
backend/
  app/
    main.py                  # creación de la app, CORS, manejo de errores, /api/health
    core/config.py           # configuración (.env)
    core/errors.py           # errores de dominio y formato de respuesta
    api/routes/documents.py  # endpoints REST
    schemas/document.py      # modelos de respuesta
    models/job.py            # estado del job de extracción
    services/validation.py   # validación del PDF (extensión, firma, tamaño, páginas, cifrado)
    services/mineru_client.py# cliente HTTP de la API de MinerU
    services/extraction.py   # orquestación, descompresión y estadísticas
    services/storage.py      # persistencia en disco
  scripts/eval_cer.py        # cálculo de CER
  tests/                     # pytest
frontend/src/
  api/client.ts              # cliente de la API (con progreso de subida)
  components/                # UploadForm, ProgressIndicator, ResultViewer, DocumentList
  App.tsx
docs/                        # plan, avances del P1, comparativo del P2
samples/                     # PDF de ejemplo
```
