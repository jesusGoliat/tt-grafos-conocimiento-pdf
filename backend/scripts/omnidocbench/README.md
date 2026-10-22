# Evaluación del CER con OmniDocBench (OE-01)

Evaluación de la conversión de PDF con MinerU sobre una muestra de 42 páginas en inglés de
OmniDocBench (Ouyang et al., CVPR 2025; https://huggingface.co/datasets/opendatalab/OmniDocBench,
solo para investigación). Resultados en el Cap. 7, sección 7.5, del reporte técnico.

| Archivo | Qué hace |
|---|---|
| `sample.py <dir_omnidocbench> <dir_run>` | Muestra estratificada (semilla 42, 6 páginas por tipo, al menos 200 caracteres) y `sample.json`; usa la misma lista simétrica que `build_refs.py` |
| `build_refs.py <sample.json> <OmniDocBench.json> <dir_run> [<cer_results.csv>]` | Regenera las referencias desde los 42 ids ya fijados (sin volver a sortear) y comprueba `ref_chars`; `--legacy` reproduce la lista del run original |
| `run.py <dir_run>` | Descarga las imágenes, las convierte a PDF de una página y las extrae con `MinerUApiExtractor` (requiere `MINERU_API_TOKEN`); escribe `run_manifest.json` |
| `score.py <dir_run>` | CER por página con `blocks_text`, `normalize` y `levenshtein` de `scripts/eval_cer.py`; escribe `cer_results.csv` con `ref_math_spans` y `math_density` |
| `aggregate.py <cer_results.csv>` | CER global, media y mediana por tipo de documento, por diseño y por densidad de fórmulas |
| `grafica_cer.py <cer_results.csv> <salida.pdf>` | Gráfica de la Figura 7.1 del reporte |

`score.py` usa la misma selección de bloques que `eval_cer.py` (`blocks_text`): cuerpo, títulos,
listas, código y captions/notas de tablas, figuras y gráficos; excluye tablas, ecuaciones aisladas y
encabezados/pies/números de página. Las referencias se regeneran con `build_refs.py` a partir de
los ids de `sample.json`, de modo que la muestra no depende de volver a ejecutar el sorteo.

`sample.json` y `cer_results.csv` son la muestra y los resultados de la ejecución del 22 de octubre
de 2026: CER global 7.56 %, media 8.03 %, mediana 4.48 %; 3.13 % en las 22 páginas sin fórmulas y
14.94 % en las 13 de densidad alta. `run_manifest.json` registra la fecha, la configuración de
MinerU, el hash de `OmniDocBench.json` y los ids de la muestra.
