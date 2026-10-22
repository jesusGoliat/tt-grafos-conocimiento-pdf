"""Agrega cer_results.csv: CER global (micro), media y mediana por grupo.

Uso:
    python3 aggregate.py <cer_results.csv>

«CER global» es micro: suma de distancias / suma de caracteres de referencia.
La media y la mediana son por página (sin ponderar).
"""
import csv
import statistics
import sys
from collections import defaultdict

rows = list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    for k in ("ref_chars", "dist", "ref_math_spans"):
        r[k] = int(r[k])
    r["cer"] = float(r["cer"])
    r["math_density"] = float(r.get("math_density") or 0.0)


def agg(rs):
    return (len(rs),
            sum(r["dist"] for r in rs) / sum(r["ref_chars"] for r in rs) * 100,
            statistics.mean(r["cer"] for r in rs) * 100,
            statistics.median(r["cer"] for r in rs) * 100)


def show(title, groups):
    print(f"\n== {title}")
    for k, rs in groups:
        n, micro, mean, med = agg(rs)
        print(f"{k:24s} n={n:2d}  CER global={micro:5.2f}%  media={mean:5.2f}%  mediana={med:5.2f}%")


def math_group(r):
    if r["ref_math_spans"] == 0:
        return "sin fórmulas"
    return "baja (<=5/1000)" if r["math_density"] <= 5 else "alta (>5/1000)"


def group_by(rs, fn):
    g = defaultdict(list)
    for r in rs:
        g[fn(r)].append(r)
    return g


show("Total", [("todas", rows),
               ("sin fórmulas", [r for r in rows if r["ref_math_spans"] == 0]),
               ("con fórmulas", [r for r in rows if r["ref_math_spans"] > 0])])
ORDER = {"sin fórmulas": 0, "baja (<=5/1000)": 1, "alta (>5/1000)": 2}
show("Densidad de fórmulas",
     sorted(group_by(rows, math_group).items(), key=lambda kv: ORDER[kv[0]]))

for key in ("data_source", "layout"):
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    show(key, sorted(g.items(), key=lambda kv: agg(kv[1])[1]))

print("\npáginas con CER < 5 %:", sum(r["cer"] < 0.05 for r in rows), "de", len(rows))
print("caracteres de referencia:", sum(r["ref_chars"] for r in rows))
