"""Character Error Rate (CER) del texto extraído (objetivo específico 2.1.1 del protocolo).

    CER = (S + D + I) / N    (distancia de Levenshtein entre caracteres / longitud de la referencia)

La comparación usa el cuerpo, los títulos, las listas, el código y las captions/notas
de tablas y figuras; excluye tablas, ecuaciones aisladas y encabezados/pies/números
de página (véase blocks_text). La exclusión se aplica igual con y sin --page: ambos
modos leen content_list.json y pasan por blocks_text. Solo si falta ese archivo se usa
document.md, que no permite filtrar y por tanto no es comparable con la referencia.

Uso (desde backend/):
    # Contra una transcripción manual de la página 1 (recomendado para la evaluación formal)
    python scripts/eval_cer.py data/results/<id> --page 1 --ref referencia_p1.txt

    # Contra la capa de texto del PDF (referencia aproximada, solo para PDFs nativos digitales)
    python scripts/eval_cer.py data/results/<id> --page 1 --ref-from-pdf data/uploads/<id>.pdf

    # Todo el documento contra la capa de texto
    python scripts/eval_cer.py data/results/<id> --ref-from-pdf data/uploads/<id>.pdf
"""
import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """Quita etiquetas HTML, imágenes Markdown y algunos caracteres de marcado; normaliza Unicode y espacios.

    Conserva los nombres de los comandos y las llaves de LaTeX, por lo que las
    diferencias de notación matemática siguen contando como error.
    """
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"[#*_`|>$\\]", " ", text)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"-\s*\n\s*", "", text)  # palabras cortadas por guion al final de línea
    return re.sub(r"\s+", " ", text).strip()


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def cer(hypothesis: str, reference: str) -> float:
    return levenshtein(hypothesis, reference) / max(len(reference), 1)


# Captions y notas que tienen contraparte en la referencia de OmniDocBench.
# En OmniDocBench un gráfico se anota como figure; MinerU lo emite como chart,
# por eso chart_caption/chart_footnote también se incluyen.
CAPTION_KEYS = ("table_caption", "table_footnote", "image_caption", "image_footnote",
                "chart_caption", "chart_footnote")


def blocks_text(blocks: list[dict]) -> str:
    """Texto comparable de una lista de bloques de content_list.json.

    Incluye cuerpo, títulos (type "text" con text_level), listas, código y las
    captions/notas de tablas, figuras y gráficos. Excluye tablas, ecuaciones
    aisladas y encabezados/pies/números de página, que no forman parte de la
    referencia de esta muestra.
    """
    parts = []
    for block in blocks:
        kind = block.get("type")
        if kind == "text":
            parts.append(block.get("text") or "")
        elif kind == "list":
            items = block.get("list_items") or []
            parts.extend(items if isinstance(items, list) else [str(items)])
        elif kind == "code":
            parts.append(block.get("code_body") or "")
        for key in CAPTION_KEYS:
            parts.extend(block.get(key) or [])
    return "\n".join(parts)


def extracted_text(result_dir: Path, page: int | None) -> str:
    """Texto extraído, filtrado con blocks_text tanto por página como en el documento completo.

    Se lee siempre content_list.json para que la exclusión de tablas, ecuaciones y
    encabezados/pies sea la misma en los dos modos. Solo si no existe ese archivo se
    recurre a document.md, que no permite filtrar y por tanto no es comparable.
    """
    content_list = result_dir / "content_list.json"
    if not content_list.is_file():
        if page is not None:
            raise SystemExit(f"No hay content_list.json en {result_dir}; no se puede filtrar por página.")
        return (result_dir / "document.md").read_text(encoding="utf-8")
    blocks = json.loads(content_list.read_text(encoding="utf-8"))
    if page is not None:
        blocks = [b for b in blocks if b.get("page_idx") == page - 1]
    return blocks_text(blocks)


def pdf_text(pdf_path: Path, page: int | None) -> str:
    import pymupdf

    with pymupdf.open(pdf_path) as doc:
        pages = [doc[page - 1]] if page else list(doc)
        return "\n".join(p.get_text() for p in pages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("result_dir", type=Path, help="Carpeta data/results/<id>")
    parser.add_argument("--page", type=int, help="Página (1-indexada); si se omite se evalúa el documento completo")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ref", type=Path, help="Archivo .txt con la transcripción de referencia")
    source.add_argument("--ref-from-pdf", type=Path, help="PDF cuya capa de texto se usa como referencia")
    args = parser.parse_args()

    reference = args.ref.read_text(encoding="utf-8") if args.ref else pdf_text(args.ref_from_pdf, args.page)
    hyp, ref = normalize(extracted_text(args.result_dir, args.page)), normalize(reference)
    if len(hyp) * len(ref) > 2e9:
        print("Texto demasiado largo para Levenshtein en Python puro; evalúa por página (--page).", file=sys.stderr)
        return 1
    distance = levenshtein(hyp, ref)
    print(f"Caracteres referencia: {len(ref)}")
    print(f"Caracteres extraídos:  {len(hyp)}")
    print(f"Distancia de edición:  {distance}")
    print(f"CER: {distance / max(len(ref), 1):.4f} ({distance / max(len(ref), 1):.2%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
