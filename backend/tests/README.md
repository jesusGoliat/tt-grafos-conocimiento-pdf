# Pruebas del backend

## Ejecución ordinaria

```bash
cd backend && pytest -m "not integration" -q
```

31 pruebas, sin red y sin token: la API de MinerU se simula con `respx` y los PDF se
generan con PyMuPDF. Tarda alrededor de un segundo.

| Archivo | Casos | Qué verifica |
|---|---|---|
| `test_validation.py` | 10 | Aceptación y rechazo de PDF por extensión, tipo, firma, tamaño, páginas y cifrado |
| `test_extraction_flow.py` | 7 | Flujo completo con MinerU simulado, fallos, ZIP con subcarpeta y protección contra *zip slip* |
| `test_api.py` | 9 | Endpoints, códigos de error y rutas de archivos |
| `test_eval_cer.py` | 5 | Normalización, distancia de edición, selección de bloques y coherencia entre modos de `eval_cer.py` |

## Prueba de integración

```bash
export MINERU_API_TOKEN=<token>
cd backend && pytest -m integration -q
```

Extrae `samples/2027-A038.pdf` con la API real de MinerU. Requiere token y consume
cuota del servicio. Queda excluida de la ejecución ordinaria por `pytest.ini`.

## Última ejecución registrada

`pytest -m "not integration"`: 31 aprobadas, 0 fallos.

`pytest -m integration`: 1 aprobada en 13.74 s, con la API real de MinerU.

```text
$ MINERU_API_TOKEN=<configurado> pytest -m integration -q

.                                                                        [100%]
1 passed, 31 deselected, 1 warning in 13.74s
```

Fecha de la ejecución: 22 de octubre de 2026. El token no se registra ni se versiona.
