"""Character Error Rate (CER) del texto extraído (objetivo específico 2.1.1 del protocolo).

    CER = (S + D + I) / N    (distancia de Levenshtein entre caracteres / longitud de la referencia)

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
    """Quita marcas de Markdown/HTML/LaTeX y normaliza Unicode y espacios para comparar solo el contenido."""
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


def extracted_text(result_dir: Path, page: int | None) -> str:
    """Texto extraído: por página desde content_list.json, o el documento completo desde document.md."""
    if page is None:
        return (result_dir / "document.md").read_text(encoding="utf-8")
    blocks = json.loads((result_dir / "content_list.json").read_text(encoding="utf-8"))
    parts = []
    for block in blocks:
        if block.get("page_idx") != page - 1:
            continue
        parts.append(block.get("text") or block.get("table_body") or "")
        parts.extend(block.get("table_caption") or [])
        parts.extend(block.get("image_caption") or [])
    return "\n".join(parts)


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
