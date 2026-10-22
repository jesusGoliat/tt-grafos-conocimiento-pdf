import csv, sys
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "serif", "font.size": 9, "pdf.fonttype": 42})
rows = list(csv.DictReader(open(sys.argv[1])))
NAMES = {"colorful_textbook": "Libros de texto a color", "magazine": "Revistas", "academic_literature": "Artículos académicos",
         "newspaper": "Periódicos", "exam_paper": "Exámenes", "book": "Libros", "PPT2PDF": "Presentaciones"}
g = defaultdict(lambda: [0, 0])
for r in rows:
    g[r["data_source"]][0] += int(r["dist"]); g[r["data_source"]][1] += int(r["ref_chars"])
items = sorted(((NAMES[k], d / n * 100) for k, (d, n) in g.items()), key=lambda x: x[1])
total = sum(int(r["dist"]) for r in rows) / sum(int(r["ref_chars"]) for r in rows) * 100
fig, ax = plt.subplots(figsize=(5.6, 2.7))
y = range(len(items))
ax.barh(y, [v for _, v in items], color="#3b6fd8", height=0.62)
for i, (_, v) in enumerate(items):
    ax.text(v + 0.25, i, f"{v:.2f}", va="center", fontsize=8, bbox=dict(facecolor="white", edgecolor="none", pad=0.5), zorder=3)
ax.axvline(total, color="#444", ls="--", lw=0.9)
ax.text(total + 0.25, len(items) - 0.45, f"global: {total:.2f}", fontsize=8, color="#444")
ax.set_yticks(list(y)); ax.set_yticklabels([k for k, _ in items])
ax.set_xlabel("CER (%)"); ax.set_xlim(0, max(v for _, v in items) * 1.18)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(sys.argv[2])
