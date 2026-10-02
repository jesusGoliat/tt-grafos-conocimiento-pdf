# Plan de trabajo — Prototipos 1 y 2

**Trabajo Terminal:** Generación de Grafos de Conocimiento a partir de Documentos en Formato PDF mediante Modelos de Lenguaje Extensos y Procesamiento de Lenguaje Natural
**Alumno:** González Arellano Jesús Ángel
**Etapa:** Trabajo Terminal I (Infraestructura y Extracción)
**Metodología:** Modelo de Prototipado Evolutivo (protocolo, §5)

---

## 1. Contexto

El protocolo divide el desarrollo en cuatro prototipos evolutivos. En TT I se construyen:

| Prototipo | Objetivo (protocolo §5.1) | Alcance en este plan |
|---|---|---|
| **P1**: Infraestructura web y módulo de extracción de PDF | Arquitectura base frontend/backend + extracción de texto de PDF con manejo de distintas estructuras documentales | **Se implementa** |
| **P2**: Pipeline de NLP y extracción inicial de entidades | Segmentación, preprocesamiento, NER y primeras pruebas de extracción de relaciones | **Solo se investiga**: documento comparativo de opciones para discutir con el sinodal |

Objetivos específicos relacionados:

- **2.1.1**: módulo de extracción de texto de PDF, evaluado con *Character Error Rate* (CER) → P1.
- **2.1.2**: pipeline NLP para entidades, conceptos y relaciones, evaluado con Precisión/Recall/F1 → P2.
- **2.1.6**: interfaz web que integra carga, procesamiento y visualización, evaluada con un checklist funcional (*Task Completion Rate*) → la base se construye en P1.

## 2. Decisiones técnicas acordadas

| Tema | Decisión | Motivo |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Requisito; tipado con Pydantic y documentación OpenAPI automática |
| Frontend | React + Vite + TypeScript | Vite es la herramienta vigente (CRA está descontinuado); TS tipa el contrato con la API |
| Extracción de PDF | **API en la nube de MinerU** (`mineru.net/api/v4`) | El equipo de desarrollo no tiene GPU (Intel HD 520), tiene 7 GB de RAM y ~6.7 GB libres en disco; MinerU local en CPU es lento y sus modelos ocupan varios GB |
| Formato de salida | Markdown + JSON (`content_list.json`, `layout.json`) + imágenes | MinerU entrega ambos; el Markdown sirve para visualizar y el JSON conserva la estructura (tipo de bloque, página, nivel de título) que necesita P2 |
| Persistencia en P1 | Sistema de archivos (`data/`) con `metadata.json` por documento | Suficiente para el prototipo; la base de datos de grafos (Neo4j) se deja para P3 |
| Documentación | Markdown en `/docs` | Versionable y convertible con pandoc |

Supuesto: se necesita un token de la API de MinerU, que se configura en `backend/.env`. Límites del servicio: ≤200 MB y ≤200 páginas por archivo, 1000 páginas al día con prioridad.

## 3. Prototipo 1: Infraestructura web y extracción de PDF

### Fases

| Fase | Actividades | Entregable |
|---|---|---|
| **0. Plan** | Lectura del protocolo, decisiones técnicas, plan | `docs/plan_de_trabajo.md` |
| **1. Backend base** | Estructura modular (`core`, `api/routes`, `schemas`, `services`, `models`); configuración por `.env`; endpoints de carga, estado, resultado, recursos y listado; validación de PDF; manejo uniforme de errores; persistencia en disco | `backend/app/` funcional con Swagger en `/docs` |
| **2. Integración MinerU** | Cliente HTTP: solicitar URL prefirmada, subir el archivo, consultar el estado periódicamente, descargar el ZIP, descomprimirlo y normalizar la salida; procesamiento en segundo plano; estadísticas por tipo de bloque | `services/mineru_client.py`, `services/extraction.py` |
| **3. Frontend** | Vista de carga (arrastrar y soltar + validación), indicador de progreso (subida y estados del job), visor por pestañas (Markdown renderizado, Markdown crudo, JSON, estadísticas), listado de documentos | `frontend/` (Vite + React + TS) |
| **4. Pruebas** | Pruebas unitarias con MinerU simulado (validación, flujo completo, errores, endpoints); prueba de integración real con el PDF de ejemplo; script de CER | `backend/tests/`, `backend/scripts/eval_cer.py` |
| **5. Documentación** | README de instalación y ejecución; reporte de avances | `README.md`, `docs/avances_prototipo1.md` |

### API REST (contrato inicial)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/documents` | Sube un PDF (multipart), lo valida e inicia la extracción. Responde `202` con `id` y estado |
| `GET` | `/api/documents` | Lista los documentos y su estado |
| `GET` | `/api/documents/{id}` | Estado del job (`queued`, `uploading`, `processing`, `done`, `failed`), progreso y error |
| `GET` | `/api/documents/{id}/result` | Markdown, `content_list` (JSON) y estadísticas; `409` si aún no termina |
| `GET` | `/api/documents/{id}/assets/{path}` | Imágenes extraídas por MinerU |
| `GET` | `/api/health` | Salud del servicio y si hay token configurado |

### Criterios de aceptación

1. Backend y frontend se levantan siguiendo el README.
2. Se sube `samples/2027-A038.pdf`, se ve el progreso y después el contenido extraído (títulos, párrafos, Tabla 1) sin errores.
3. Archivos inválidos (no PDF, vacíos, corruptos, demasiado grandes) se rechazan con mensajes claros.
4. Las pruebas unitarias pasan; la de integración pasa cuando hay token.

## 4. Prototipo 2: Opciones de extracción de entidades (investigación)

### Fases

| Fase | Actividades | Entregable |
|---|---|---|
| **1. Definición del problema** | Tipología de entidades a partir del protocolo: entidades nombradas genéricas (Persona, Organización, Lugar, Fecha, Obra/Producto, Evento) y conceptos clave del dominio; idioma principal: español | Sección inicial del comparativo |
| **2. Revisión de enfoques** | Deterministas (regex, reglas, gramáticas, gazetteers), ML clásico (CRF, SVM), deep learning/transformers (spaCy, BETO, RoBERTa-BNE, XLM-R, GLiNER), LLMs (prompting, salida estructurada, few-shot, fine-tuning), híbridos | Fichas por enfoque con fuentes citadas |
| **3. Comparación** | Tabla: requisitos de datos, costo computacional, precisión esperada, herramientas, idoneidad | Tabla comparativa |
| **4. Recomendación** | Recomendación preliminar y preguntas abiertas para el sinodal | `docs/prototipo2_opciones_extraccion_entidades.md` |

### Insumo desde P1

El `content_list.json` de MinerU (bloques con tipo, página y nivel de título) será la entrada del pipeline de NLP: permite segmentar por sección, excluir encabezados y pies de página y tratar las tablas aparte.

## 5. Entregables

| # | Entregable | Ubicación |
|---|---|---|
| 1 | Plan de trabajo | `docs/plan_de_trabajo.md` |
| 2 | Código del Prototipo 1 | `backend/`, `frontend/` |
| 3 | README de instalación y ejecución | `README.md` |
| 4 | Pruebas y PDF de ejemplo | `backend/tests/`, `samples/` |
| 5 | Reporte de avances del Prototipo 1 | `docs/avances_prototipo1.md` |
| 6 | Comparativo de extracción de entidades | `docs/prototipo2_opciones_extraccion_entidades.md` |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Dependencia de un servicio externo (disponibilidad, cuota, privacidad de los documentos) | El extractor está detrás de una interfaz, así que se puede reemplazar por MinerU local u otro motor sin tocar rutas ni frontend; documentado como decisión a revisar |
| Latencia de la API (de segundos a minutos) | Procesamiento asíncrono con consulta de estado y progreso visible en la interfaz |
| Expiración de las URLs de resultados | El ZIP se descarga y se guarda localmente en cuanto termina la extracción |
| Recursos limitados del equipo | Sin modelos locales en P1; P2 evalúa opciones viables en CPU |
