# Evaluación del CER con OmniDocBench (OE-01)

Evaluación de la conversión de PDF con MinerU sobre una muestra de 42 páginas en inglés de
OmniDocBench (Ouyang et al., CVPR 2025; <https://huggingface.co/datasets/opendatalab/OmniDocBench>,
**solo para investigación**). Resultados en el capítulo 7 del reporte técnico de TT I.

Los artefactos de la ejecución del 22 de octubre de 2026 están en
[`resultados_cer_2026-10-22/`](resultados_cer_2026-10-22/); ese directorio se pasa como
`<dir_run>` a los scripts.

## Scripts

| Archivo | Qué hace |
|---|---|
| `sample.py <dir_omnidocbench> <dir_run>` | Muestra estratificada (semilla 42, 6 páginas por tipo, al menos 200 caracteres), `sample.json` y las referencias `<id>.ref.txt`; usa `REF_CATS` de `build_refs.py` |
| `build_refs.py <sample.json> <OmniDocBench.json> <dir_run> [<cer_results.csv>]` | Regenera las referencias desde los 42 ids ya fijados (sin volver a sortear) y comprueba `ref_chars` |
| `run.py <dir_run>` | Descarga las imágenes, las convierte a PDF de una página y las extrae con `MinerUApiExtractor` (requiere `MINERU_API_TOKEN`) |
| `make_manifest.py <dir_run>` | Escribe `run_manifest.json` con la configuración, el hash de `OmniDocBench.json` y el estado. Requiere `ODB_SHA256` |
| `score.py <dir_run>` | CER por página con `blocks_text`, `normalize` y `levenshtein` de `scripts/eval_cer.py`; escribe `cer_results.csv` |
| `aggregate.py <cer_results.csv>` | CER global, media y mediana por tipo de documento, por diseño y por densidad de fórmulas |
| `grafica_cer.py <cer_results.csv> <salida.pdf>` | Gráfica de la Figura 7.1 del reporte (requiere `matplotlib`, ver `requirements-eval.txt`) |

## Recalcular las métricas

Desde este directorio, sin red y sin token:

```bash
python3 aggregate.py resultados_cer_2026-10-22/cer_results.csv
```

Para recalcular además la distancia de edición de cada página a partir de las salidas
de MinerU (unos 5 minutos):

```bash
cp -r resultados_cer_2026-10-22 /tmp/cer && python3 score.py /tmp/cer
python3 aggregate.py /tmp/cer/cer_results.csv
```

`score.py` escribe `cer_results.csv` en el directorio que recibe, por eso se copia
antes: así no se sobrescribe el archivo publicado.

## Qué se compara

`score.py` usa la misma selección de bloques que `eval_cer.py` (`blocks_text`): cuerpo,
títulos, listas, código y pies de tabla, figura y gráfico. Excluye tablas, ecuaciones
aisladas y encabezados, pies y números de página.

La exclusión es **simétrica**: las referencias se construyeron con la misma lista de
tipos (`REF_CATS`), así que la métrica mide el subconjunto de la página con
contrapartida anotada, no la página completa. Al incluir las ecuaciones, una misma
página pasa de 12.31 % a 173 %.

## Resultados

Ejecución del 22 de octubre de 2026: CER global **7.56 %**, media 8.03 %, mediana
4.48 %; 3.13 % en las 22 páginas sin fórmulas en línea y 14.94 % en las 13 de densidad
alta.

## Reproducibilidad

- `sample.json` fija los 42 ids y su orden; `run_manifest.json` registra la fecha, la
  configuración de MinerU y el SHA-256 de `OmniDocBench.json`.
- **Se publican** los resultados derivados: `sample.json`, las 42 referencias
  `<id>.ref.txt`, los 42 `results/<id>/content_list.json`, `cer_results.csv`,
  `run_manifest.json` y este README.
- **No se publican** los 42 PDF de página (`pdfs/`) ni las imágenes: son páginas de
  OmniDocBench, con licencia solo para investigación. Se regeneran con `run.py`.
- La correspondencia entre `pdfs/odb_XX.pdf` y cada id es el orden de `sample.json`.
- Regenerar las referencias exige descargar `OmniDocBench.json` y ejecutar
  `build_refs.py`; solo se conserva su hash.
- Reejecutar MinerU no garantiza resultados idénticos: depende de una API en la nube.
  Lo reproducible es el cálculo de las métricas a partir de los artefactos publicados.
