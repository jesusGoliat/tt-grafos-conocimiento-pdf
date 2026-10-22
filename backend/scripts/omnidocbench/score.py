"""CER por página de la muestra de OmniDocBench con la normalización y la distancia de eval_cer.py.

La selección de bloques es la misma que usa eval_cer.py (blocks_text): cuerpo,
títulos, listas, código y captions/notas de tablas, figuras y gráficos. Se excluyen
tablas, ecuaciones aisladas y encabezados/pies/números de página, que tampoco están
en la referencia de OmniDocBench.

Uso:
    python3 score.py <run_dir> [--legacy-csv <csv_anterior>]

Si una página no tiene content_list.json (por ejemplo, por un fallo de subida), se
reutiliza su fila del CSV anterior cuando se indica --legacy-csv. La columna `source`
indica qué filas son de la extracción nueva y cuáles heredadas.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eval_cer import blocks_text, levenshtein, normalize

parser = argparse.ArgumentParser()
parser.add_argument("run", type=Path)
parser.add_argument("--legacy-csv", type=Path)
args = parser.parse_args()
run = args.run
legacy = {}
if args.legacy_csv and args.legacy_csv.is_file():
    legacy = {r["id"]: r for r in csv.DictReader(open(args.legacy_csv))}

MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$|\\\(.*?\\\)", re.S)
LATEXISH = re.compile(r"[\\^_{}=]")
# Signo de moneda escapado: "$\$$" en las anotaciones, "\$" en MinerU.
CURRENCY = re.compile(r"\$*\\\$\$*")


def is_math(seg):
    return bool(LATEXISH.search(seg)) or (len(seg) <= 5 and not seg.strip("$").strip().isdigit())


rows = []
for m in json.loads((run / "sample.json").read_text()):
    result = run / "results" / m["id"] / "content_list.json"
    if not result.is_file():
        old = legacy.get(m["id"])
        if old is None:
            print(f"{m['id']}: sin salida y sin fila anterior; se omite", flush=True)
            continue
        ref_chars = int(old["ref_chars"])
        spans = int(old["ref_math_spans"])
        rows.append({
            "id": m["id"],
            "data_source": m["data_source"],
            "layout": m["layout"],
            "ref_chars": ref_chars,
            "hyp_chars": int(old["hyp_chars"]),
            "dist": int(old["dist"]),
            "cer": float(old["cer"]),
            "ref_math_spans": spans,
            "math_density": spans / (ref_chars / 1000) if ref_chars else 0.0,
            "source": "legacy",
        })
        print(f"{m['id']}: se reutiliza la fila anterior", flush=True)
        continue

    blocks = json.loads(result.read_text())
    ref_raw = (run / f"{m['id']}.ref.txt").read_text()
    hyp = normalize(blocks_text(blocks))
    ref = normalize(ref_raw)
    d = levenshtein(hyp, ref)
    n_math = sum(is_math(x) for x in MATH.findall(CURRENCY.sub(" ", ref_raw)))
    rows.append({
        "id": m["id"],
        "data_source": m["data_source"],
        "layout": m["layout"],
        "ref_chars": len(ref),
        "hyp_chars": len(hyp),
        "dist": d,
        "cer": d / max(len(ref), 1),
        "ref_math_spans": n_math,
        "math_density": n_math / (len(ref) / 1000) if ref else 0.0,
        "source": "new",
    })
    print(f"{m['data_source']:20s} {m['layout']:16s} {len(ref):6d} {d / max(len(ref), 1):.4f} {n_math}", flush=True)

if not rows:
    sys.exit("No hay filas para escribir.")

with open(run / "cer_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
