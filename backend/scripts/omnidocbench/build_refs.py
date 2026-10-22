"""Regenera las referencias de una muestra ya fijada y verifica su integridad.

Uso:
    python3 -I build_refs.py <sample.json> <OmniDocBench.json> <run_dir> [<cer_results.csv>] [--legacy]

No vuelve a sortear la muestra: usa los ids de sample.json y localiza cada página
por el stem de image_path.

REF_CATS es la lista simétrica: incluye solo categorías de OmniDocBench que tienen
contraparte en content_list.json de MinerU. Se excluyen equation_caption y
code_txt_caption porque MinerU no emite captions de ecuación/código. Con --legacy
se usa la lista del run original (incluye esas dos categorías) para comprobar que
el dataset reproduce exactamente los ref_chars del CSV.
"""
import csv
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent / "eval_cer.py"
spec = importlib.util.spec_from_file_location("eval_cer", EVAL)
_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_eval)
normalize = _eval.normalize

# Lista simétrica: cada categoría tiene contraparte en la hipótesis.
REF_CATS = {"text_block", "title", "reference", "figure_caption", "figure_footnote",
            "table_caption", "table_footnote", "list_group", "code_txt"}
# Lista del run original, solo para el control de integridad.
LEGACY_CATS = REF_CATS | {"equation_caption", "code_txt_caption"}


def ref_blocks(page, cats):
    blocks = [b for b in page["layout_dets"]
              if b["category_type"] in cats and not b.get("ignore")]
    blocks.sort(key=lambda b: (b.get("order") is None, b.get("order") or 0))
    return blocks


def ref_text(page, cats):
    parts = []
    for b in ref_blocks(page, cats):
        t = b.get("text")
        if not t and b.get("merge_list"):
            t = "\n".join(m.get("text", "") for m in b["merge_list"])
        if t:
            parts.append(t)
    return "\n".join(parts)


def main() -> int:
    legacy = "--legacy" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--legacy"]
    sample_path = Path(args[0])
    odb_path = Path(args[1])
    run_dir = Path(args[2])
    csv_path = Path(args[3]) if len(args) > 3 else None
    cats = LEGACY_CATS if legacy else REF_CATS

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    pages = json.loads(odb_path.read_text(encoding="utf-8"))
    by_stem = {Path(p["page_info"]["image_path"]).stem: p for p in pages}

    old = {}
    if csv_path and csv_path.is_file():
        old = {r["id"]: int(r["ref_chars"]) for r in csv.DictReader(open(csv_path))}

    run_dir.mkdir(parents=True, exist_ok=True)
    missing = []
    rows = []
    cat_blocks = Counter()
    cat_chars = Counter()
    for m in sample:
        pid = m["id"]
        page = by_stem.get(pid)
        if page is None:
            missing.append(pid)
            continue
        for b in ref_blocks(page, cats):
            cat_blocks[b["category_type"]] += 1
            cat_chars[b["category_type"]] += len(b.get("text") or "")
        ref = ref_text(page, cats)
        (run_dir / f"{pid}.ref.txt").write_text(ref, encoding="utf-8")
        n = len(normalize(ref))
        rows.append((pid, n, old.get(pid)))

    print(f"modo: {'legacy' if legacy else 'simétrico'}")
    print(f"páginas en la muestra: {len(sample)}; encontradas: {len(rows)}; faltantes: {len(missing)}")
    if missing:
        print("FALTAN:", *missing, sep="\n  ")
    mismatches = [r for r in rows if r[2] is not None and r[1] != r[2]]
    print(f"ref_chars: {len(rows) - len(mismatches)} coinciden, {len(mismatches)} no coinciden")
    for pid, n, o in mismatches:
        print(f"  delta {pid}: nuevo={n} antiguo={o} diferencia={n - (o or 0)}")
    print("\nbloques por categoría en la muestra:")
    for k, v in cat_blocks.most_common():
        print(f"  {k:22s} bloques={v:5d} chars_texto={cat_chars[k]:7d}")
    if missing:
        return 1
    # En modo legacy la coincidencia debe ser exacta; el modo simétrico cambia
    # a propósito la lista de categorías y solo informa del delta.
    return 1 if legacy and mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
