"""Selecciona la muestra estratificada de páginas en inglés de OmniDocBench y construye el texto de referencia."""
import json, random, sys, collections
from pathlib import Path
from build_refs import REF_CATS
odb = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
# Única definición de la lista simétrica: build_refs.REF_CATS.
TEXT_CATS = REF_CATS
SOURCES = ["academic_literature", "book", "PPT2PDF", "magazine", "exam_paper", "newspaper", "colorful_textbook"]
PER_SOURCE = 6
pages = json.load(open(odb / "OmniDocBench.json"))

def ref_text(page):
    blocks = [b for b in page["layout_dets"] if b["category_type"] in TEXT_CATS and not b.get("ignore")]
    blocks.sort(key=lambda b: (b.get("order") is None, b.get("order") or 0))
    parts = []
    for b in blocks:
        t = b.get("text")
        if not t and b.get("merge_list"):
            t = "\n".join(m.get("text", "") for m in b["merge_list"])
        if t: parts.append(t)
    return "\n".join(parts)

rng = random.Random(42)
sample = []
for src in SOURCES:
    cands = [p for p in pages if p["page_info"]["page_attribute"].get("language") == "english"
             and p["page_info"]["page_attribute"].get("data_source") == src and len(ref_text(p)) >= 200]
    cands.sort(key=lambda p: p["page_info"]["image_path"])
    sample += rng.sample(cands, PER_SOURCE)
meta = []
for p in sample:
    name = Path(p["page_info"]["image_path"]).stem
    (out / f"{name}.ref.txt").write_text(ref_text(p), encoding="utf-8")
    a = p["page_info"]["page_attribute"]
    meta.append({"id": name, "image": p["page_info"]["image_path"], "data_source": a.get("data_source"),
                 "layout": a.get("layout"), "special_issue": a.get("special_issue", [])})
(out / "sample.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
print(len(meta), collections.Counter(m["layout"] for m in meta))
