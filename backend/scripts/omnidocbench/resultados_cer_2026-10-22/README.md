# Evaluación CER — archivo de resultados (22 de octubre de 2026)

Carpeta con los artefactos que permiten recalcular las métricas del CER **sin volver a
ejecutar MinerU y sin conexión a la red**.

## Contenido

| Elemento | Qué es |
|---|---|
| `sample.json` | Los 42 identificadores de la muestra y su orden. |
| `<id>.ref.txt` | La referencia por página: texto anotado de OmniDocBench. |
| `results/<id>/content_list.json` | Salida estructurada de MinerU por página. |
| `cer_results.csv` | CER por página y por grupo. |
| `run_manifest.json` | Configuración de MinerU, hash de `OmniDocBench.json` y estado. |

Los scripts de cálculo están en el directorio padre: `score.py`, `aggregate.py`,
`grafica_cer.py`, `build_refs.py`, `sample.py`, `run.py` y `make_manifest.py`.

## Recalcular

Desde esta carpeta:

```bash
python3 ../score.py .                    # recalcula distancias (≈5 min)
python3 ../aggregate.py cer_results.csv
python3 ../grafica_cer.py cer_results.csv figura.pdf   # requiere matplotlib
```

`score.py` lee `sample.json`, los `<id>.ref.txt` y `results/<id>/content_list.json`, y
escribe `cer_results.csv` en este mismo directorio. Si se quiere conservar el CSV
publicado, cópiate antes la carpeta a otro lugar.

`aggregate.py` no necesita nada más. Devuelve 7.56 % global y 3.13 % sin fórmulas.

## Qué no está aquí

- **Los 42 PDF de página** (`pdfs/`): son páginas de OmniDocBench y el conjunto tiene
  licencia solo para investigación, sin permiso expreso de redistribución. Se generan
  con `run.py`, que descarga las imágenes y las convierte a PDF de una página.
- **Las imágenes extraídas** por MinerU: no las usa ningún script de evaluación.

La correspondencia entre `pdfs/odb_XX.pdf` y cada id es el **orden de `sample.json`**.

## Reproducibilidad

- El SHA-256 de `OmniDocBench.json` está en `run_manifest.json`.
- Las referencias se pueden regenerar con `build_refs.py` a partir de los 42 ids y del
  archivo de anotaciones, sin volver a sortear la muestra. Ese archivo no se distribuye
  aquí; debe descargarse de <https://huggingface.co/datasets/opendatalab/OmniDocBench>.
- Reejecutar MinerU no garantiza resultados idénticos: depende de una API en la nube.
- Los artefactos derivan de OmniDocBench y están sujetos a su licencia. Ver `NOTICE` en
  la raíz del repositorio.
