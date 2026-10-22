# Grafos de conocimiento a partir de PDF — Trabajo Terminal I

Repositorio oficial del Trabajo Terminal I *«Generación de Grafos de Conocimiento a
partir de Documentos en Formato PDF mediante LLM y NLP»* (ESCOM, IPN). Reúne el código
final del **Prototipo 1**, la evaluación del **CER** con sus artefactos y una
descripción del **Prototipo 2** con enlace a su repositorio especializado.

- **Backend:** Python 3.11+ con FastAPI (`backend/`)
- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Extracción de texto:** API en la nube de [MinerU](https://mineru.net) v4

## 1. Objetivo

Construir un sistema que, a partir de documentos PDF, genere una representación
estructurada, navegable y con procedencia verificable del conocimiento contenido en
ellos, mediante extracción de texto, procesamiento de lenguaje natural y modelos de
lenguaje extensos.

El proyecto tiene siete objetivos específicos. Cuatro se cerraron en TT I y tres
están programados para TT II; **no son entregables pendientes de este repositorio**.
El detalle está en [`docs/CONTEXTO.md`](docs/CONTEXTO.md) y en
[`docs/alcance.md`](docs/alcance.md).

## 2. Arquitectura

```
      PDF
       │
       ▼
 ┌──────────────┐   multipart    ┌──────────────────┐
 │  Frontend    │ ─────────────▶ │  Backend         │
 │  React :5173 │ ◀───────────── │  FastAPI :8001   │
 └──────────────┘   JSON/progreso └────────┬─────────┘
                                            │ HTTPS
                                            ▼
                                   ┌──────────────────┐
                                   │  API de MinerU   │
                                   └────────┬─────────┘
                                            │ ZIP
                                            ▼
                              backend/data/results/<id>/
                                document.md, content_list.json,
                                layout.json, images/
```

El backend valida el PDF, lo sube a MinerU, consulta el estado hasta que termina,
descarga el ZIP y lo normaliza a una estructura fija en disco. El frontend muestra el
avance y el resultado en cuatro pestañas.

Dos módulos paralelos: P1 (este repositorio) y P2 (repositorio especializado). La
integración de ambos corresponde al Prototipo 3, en TT II.

## 3. Estructura del repositorio

```
backend/
  app/
    main.py                   # app, CORS, manejo de errores, /api/health
    core/config.py            # configuración desde .env
    core/errors.py            # errores de dominio y formato de respuesta
    api/routes/documents.py   # endpoints REST
    schemas/document.py       # modelos de respuesta
    models/job.py             # estado del job de extracción
    services/validation.py    # validación del PDF
    services/mineru_client.py # cliente de la API de MinerU
    services/extraction.py    # orquestación, descompresión y estadísticas
    services/storage.py       # persistencia en disco
  scripts/
    eval_cer.py               # cálculo del CER
    omnidocbench/             # evaluación sobre OmniDocBench (ver sección 6)
  tests/                      # 30 pruebas automatizadas
frontend/src/                 # React + Vite + TypeScript
docs/
  CONTEXTO.md                 # fuente normativa del proyecto
  alcance.md                  # qué cubre TT I y qué queda para TT II
  notas/figuras_p2.py         # nota histórica: figuras del Prototipo 2, no ejecutable como parte del sistema
samples/2027-A038.pdf         # documento de ejemplo
```

## 4. Instalación

Requisitos: Python 3.11 o superior, Node.js **20.19 o superior** o 22.12+, y un token
de la API de MinerU (se obtiene en <https://mineru.net>, sección *API Management*).

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edita .env y escribe tu token en MINERU_API_TOKEN=

# Frontend
cd ../frontend
npm ci
```

`npm ci` instala exactamente las versiones fijadas en `package-lock.json`.

## 5. Ejecución

Dos terminales.

```bash
# Terminal 1 — API en http://localhost:8001 (Swagger en /docs)
cd backend && source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload
```

```bash
# Terminal 2 — interfaz en http://localhost:5173
cd frontend
npm run dev
```

Abre <http://localhost:5173>, arrastra un PDF (por ejemplo `samples/2027-A038.pdf`) y
pulsa **Extraer contenido**. La interfaz muestra el avance (subida → envío a MinerU →
extracción página por página → listo) y después el resultado en cuatro pestañas: vista
renderizada, Markdown, JSON estructurado y estadísticas. Con **Comparar con el PDF** el
documento original se muestra junto al resultado.

> El servidor de Vite redirige `/api` a `http://localhost:8001`. Si el backend corre en
> otro puerto, usa `BACKEND_URL=http://localhost:XXXX npm run dev`.

### Configuración (`backend/.env`)

| Variable | Por defecto | Descripción |
|---|---|---|
| `MINERU_API_TOKEN` | (vacío) | Token de MinerU (**obligatorio**) |
| `MINERU_MODEL_VERSION` | `pipeline` | `pipeline` o `vlm` (más preciso y más lento) |
| `MINERU_LANGUAGE` | `latin` | Familia de idioma del OCR (`latin` cubre español) |
| `MINERU_BASE_URL` | `https://mineru.net/api/v4` | Punto de acceso de la API |
| `MINERU_ENABLE_TABLE` / `MINERU_ENABLE_FORMULA` | `true` | Reconocimiento de tablas y fórmulas |
| `MINERU_IS_OCR` | `false` | Forzar OCR (para PDF escaneado) |
| `MINERU_POLL_INTERVAL_S` / `MINERU_POLL_TIMEOUT_S` | `3` / `900` | Intervalo y espera máxima del sondeo |
| `MINERU_HTTP_TIMEOUT_S` | `60` | Tiempo máximo por petición HTTP a MinerU |
| `MAX_UPLOAD_MB` | `50` | Tamaño máximo del archivo subido |
| `MAX_PAGES` | `200` | Número máximo de páginas |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes permitidos, como lista JSON |
| `DATA_DIR` | `backend/data` | Dónde se guardan PDF y resultados |
| `VITE_API_URL` | (vacío) | Origen de la API si el frontend no usa el proxy de Vite |

### API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/documents` | Sube un PDF (`multipart/form-data`, campo `file`). Responde `202` |
| `GET` | `/api/documents` | Lista los documentos |
| `GET` | `/api/documents/{id}` | Estado: `queued`, `uploading`, `processing`, `done`, `failed` |
| `GET` | `/api/documents/{id}/result` | `markdown`, `content_list` (JSON) y `stats`. `409` si no ha terminado |
| `GET` | `/api/documents/{id}/assets/images/...` | Imágenes extraídas |
| `GET` | `/api/documents/{id}/pdf` | PDF original, para compararlo con el resultado |
| `GET` | `/api/health` | Estado del servicio e indicación de si hay token configurado |

Los errores de la API de documentos usan el formato
`{"error": {"code": "...", "message": "..."}}`. Las rutas inexistentes y los métodos no
permitidos devuelven el formato por defecto de FastAPI.

```bash
curl -F "file=@samples/2027-A038.pdf;type=application/pdf" http://localhost:8001/api/documents
curl http://localhost:8001/api/documents/<id>
curl http://localhost:8001/api/documents/<id>/result
```

## 6. Evaluación del CER

El CER (*character error rate*) mide la distancia de edición entre el texto extraído y
una referencia, dividida entre la longitud de la referencia. Se evalúa sobre
**OmniDocBench**, un conjunto de páginas con anotación a nivel de bloque.

- **Qué se evalúa:** la fidelidad del texto que MinerU devuelve frente al texto
  anotado de la página.
- **Documentos:** 42 páginas en inglés de 39 PDF, siete fuentes con seis páginas cada
  una, muestreadas con semilla 42 entre las páginas de al menos 200 caracteres.
- **Qué se comparan:** solo los tipos de bloque que tienen contrapartida anotada:
  cuerpo, títulos, listas, código y pies de tabla, figura y gráfico. Quedan fuera
  tablas, ecuaciones y encabezados, pies y números de página.
- **Artefactos:** `backend/scripts/omnidocbench/resultados_cer_2026-10-22/`.
- **Procedimiento:** [`backend/scripts/omnidocbench/README.md`](backend/scripts/omnidocbench/README.md).

Para recalcular las métricas desde los artefactos publicados:

```bash
cd backend/scripts/omnidocbench
python3 aggregate.py resultados_cer_2026-10-22/cer_results.csv
```

Tarda unos 5 minutos si además se recalculan las distancias con `score.py`. Solo
necesita la biblioteca estándar de Python: no requiere red, ni token, ni los PDF.

**Resultados**

| Conjunto | Páginas | CER global |
|---|---|---|
| Todas | 42 | **7.56 %** |
| Sin fórmulas en línea | 22 | 3.13 % |
| Con fórmulas en línea | 20 | 10.63 % |
| Densidad de fórmulas alta | 13 | 14.94 % |

El criterio de aceptación era CER global ≤ 10 %, y se cumple.

**Cómo interpretarlo.** El CER mide el subconjunto de la página que tiene contrapartida
anotada, no la página completa. La exclusión es simétrica —la referencia se construyó
con la misma lista de tipos—, así que la cifra es comparable consigo misma, pero no
debe citarse como fidelidad total de la página: al incluir las ecuaciones, una misma
página pasa de 12.31 % a 173 %.

## 7. Resultados finales

| Objetivo | Métrica | Resultado |
|---|---|---|
| OE-01 | CER global | 7.56 % (42 páginas) |
| OE-02 | F1 estricto con tipo en Re-DocRED | 23.62 ± 2.01 (N=10) y 31.34 ± 0.71 (N=50) |
| OE-03 | ΔF1 del juez LLM y del autoentrenamiento | +2.23, +2.07 y +2.42; 5/5 subconjuntos |
| OE-06 | Pruebas automatizadas y criterios de aceptación | 30/30 y 4/4 |

Las pruebas se ejecutan sin red ni token:

```bash
cd backend && pytest -m "not integration" -q
```

La prueba marcada `integration` requiere token de MinerU y consume cuota.

## 8. Prototipo 2

El Prototipo 2 es un módulo **independiente** de este, no una derivación. Extrae
entidades y relaciones de extremo a extremo con **GLiNER-Relex** sobre **Re-DocRED**, y
experimenta con dos mecanismos sobre un extractor pequeño: un **juez LLM**
(`gpt-oss-120b`) que verifica los candidatos dudosos de una banda de incertidumbre, y
**autoentrenamiento** con pseudo-etiquetas, con un brazo de control que las genera con
el propio extractor.

Se compararon cinco configuraciones (Z0, B0, J0, A3-ctrl y A3) con precisión,
exhaustividad y F1 estricto con tipo, e intervalos de confianza del 95 % por bootstrap
pareado sobre cinco subconjuntos. Los mejores resultados fueron 33.41 de F1 con el
juez y mejoras de +2.23, +2.07 y +2.42 puntos según la comparación, favorables en los
cinco subconjuntos.

**La implementación, los datos y la reproducción detallada de su evaluación están en:**

<https://github.com/jesusGoliat/gliner-relex-docre-benchmark>

Ese repositorio es la fuente autorizada de sus métricas, protocolos y limitaciones.
Aquí no se duplica.

## 9. Limitaciones

- El CER se midió sobre 42 páginas de OmniDocBench **en inglés**. No se demostró
  fidelidad sobre PDF digitales nativos ni sobre documentos en español.
- El CER depende de la exclusión de tablas, ecuaciones y encabezados descrita en la
  sección 6; no es una medida de la página completa.
- Los experimentos del Prototipo 2 usan 1 000 documentos por subconjunto (5 000 en
  total), no el conjunto completo de Re-DocRED.
- **Reejecutar MinerU no garantiza resultados idénticos**: depende de una API en la
  nube que puede cambiar de modelo. Lo reproducible es el cálculo de las métricas a
  partir de los artefactos archivados.
- La aplicación guarda el estado en disco y usa tareas en segundo plano: está pensada
  para un solo proceso. Con varios workers de uvicorn, cada uno marcaría como
  interrumpidos los trabajos de los demás.
- Las capturas del reporte usan un documento de ejemplo cuya portada conserva el
  marcador `20XX-XXXX`.

## 10. Licencia

El código se distribuye bajo licencia **MIT** (ver [`LICENSE`](LICENSE)). Los artefactos
derivados de OmniDocBench y el documento de ejemplo **no** están cubiertos por ella:
consulta [`NOTICE`](NOTICE).
