"""Nota histórica: figuras del Prototipo 2.

Este archivo NO forma parte del producto final del TT I y no debe ejecutarse como
parte del sistema. Se conserva como nota porque es el único código que genera las
figuras del Prototipo 2 y no existe una copia equivalente en el repositorio
especializado.

Sus datos están CODIFICADOS, no se leen de ningún CSV ni de ningún resultado. Por eso
pueden quedar desfasados sin que nada lo advierta. La fuente autorizada de las métricas
del Prototipo 2 es:

    https://github.com/jesusGoliat/gliner-relex-docre-benchmark

Si se vuelven a generar estas figuras, hay que actualizar los valores a mano y
contrastarlos con `results/` del repositorio especializado.

Uso original: python3 graficas_p2.py [dir_salida]
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

plt.rcParams.update({"font.family": "serif", "font.size": 9, "pdf.fonttype": 42})
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "figs")
AZUL, NARANJA, GRIS = "#3b6fd8", "#e08a2e", "#444"
BLANCO = dict(facecolor="white", edgecolor="none", pad=0.5)
def despinar(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)

# ---- 1) F1 por sistema ----
# (etiqueta, media, desv, usa_llm, x)
sis = [("Z0", 16.84, None, False, 0),
       ("B0", 23.62, 2.01, False, 1.6), ("J0", 25.85, 1.62, True, 2.6),
       ("A3-ctrl", 24.11, 1.61, False, 3.6), ("A3", 26.53, 1.54, False, 4.6),
       ("B0", 31.34, 0.71, False, 6.2), ("J0", 33.41, 0.15, True, 7.2)]
fig, ax = plt.subplots(figsize=(5.6, 2.9))
for n, m, sd, llm, x in sis:
    ax.bar(x, m, 0.8, color=NARANJA if llm else AZUL, yerr=sd, capsize=3,
           error_kw=dict(lw=0.9, ecolor=GRIS))
    top = m + (sd or 0)
    ax.text(x, top + 0.8, f"{m:.2f}", ha="center", fontsize=8, bbox=BLANCO, zorder=3)
ax.set_xticks([s[4] for s in sis]); ax.set_xticklabels([s[0] for s in sis])
for xs in (0.8, 5.4): ax.axvline(xs, color="#999", ls=":", lw=0.8)
ax.set_ylim(0, 47)
for x, t in ((0, "Sin ajuste"), (3.1, "N=10"), (6.7, "N=50")):
    ax.text(x, 44.5, t, ha="center", fontsize=8.5, color=GRIS)
ax.set_ylabel("F1 estricto con tipo (%)")
ax.legend(handles=[Patch(color=AZUL, label="Sin LLM en inferencia"),
                   Patch(color=NARANJA, label="Con LLM en inferencia (juez)")],
          loc="upper left", bbox_to_anchor=(0.0, 0.93), frameon=False, fontsize=8)
despinar(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "p2-f1-sistemas.pdf"))

# ---- 2) Enmascarado ----
grupos = [("N=10, s0", 2.61, 0.41), ("N=10, s1", 2.86, 1.37), ("N=10, s2", 0.79, 0.66),
          ("N=10, s3", 0.27, 0.57), ("N=10, s4", 1.39, 1.66),
          ("N=50, s0", 0.48, 1.22), ("N=50, s1", 1.09, -0.74)]
xs = [0, 1.25, 2.5, 3.75, 5, 6.9, 8.15]
w = 0.5
fig, ax = plt.subplots(figsize=(6.2, 2.9))
for x, (_, a, b) in zip(xs, grupos):
    for dx, v, c in ((-w / 2, a, AZUL), (w / 2, b, NARANJA)):
        ax.bar(x + dx, v, w, color=c)
        ax.text(x + dx, v + (0.08 if v >= 0 else -0.08), f"{v:+.2f}".replace("-", "−"),
                ha="center", va="bottom" if v >= 0 else "top", fontsize=6.5, zorder=3)
ax.axhline(0, color=GRIS, lw=0.9)
ax.axvline(5.95, color="#999", ls=":", lw=0.8)
ax.set_xticks(xs); ax.set_xticklabels([g[0] for g in grupos], rotation=30, ha="right")
ax.set_ylim(-1.3, 4.2)
ax.set_ylabel("ΔF1 del juez respecto a B0 (puntos)")
ax.legend(handles=[Patch(color=AZUL, label="Nombres visibles"),
                   Patch(color=NARANJA, label="Nombres enmascarados")],
          loc="upper right", frameon=False, fontsize=8)
despinar(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "p2-enmascarado.pdf"))

# ---- 3) Subconjuntos (slope chart) ----
paneles = [("N=10: B0 → J0", ("B0", "J0"),
            [(24.44, 27.26), (20.38, 23.59), (23.42, 24.82), (25.79, 27.34), (24.07, 26.26)]),
           ("N=50: B0 → J0", ("B0", "J0"),
            [(31.55, 33.18), (31.56, 33.36), (31.60, 33.50), (30.10, 33.55), (31.91, 33.49)]),
           ("N=10: A3-ctrl → A3", ("A3-ctrl", "A3"),
            [(24.64, 26.66), (21.49, 24.18), (23.89, 26.21), (25.74, 27.22), (24.79, 28.39)])]
cols = ["#3b6fd8", "#e08a2e", "#2a9d6f", "#b24a9a", "#7a7a7a"]
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.8))
for ax, (tit, (l, r), datos) in zip(axs, paneles):
    for i, (a, b) in enumerate(datos):
        ax.plot([0, 1], [a, b], "-o", color=cols[i], lw=1.2, ms=3.5)
    # etiquetas a la derecha, separadas si quedan muy juntas
    rng = max(max(d[1] for d in datos), max(d[0] for d in datos)) - min(min(d[1] for d in datos), min(d[0] for d in datos))
    sep = rng * 0.075
    orden = sorted(range(5), key=lambda i: datos[i][1]); pos = {}
    for k, i in enumerate(orden):
        p = datos[i][1]
        if k and p < pos[orden[k - 1]] + sep: p = pos[orden[k - 1]] + sep
        pos[i] = p
    for i in range(5):
        ax.text(1.07, pos[i], f"s{i}", color=cols[i], va="center", fontsize=8)
    lo = min(min(d) for d in datos); hi = max(max(d) for d in datos)
    ax.set_ylim(lo - 0.08 * (hi - lo) - 0.3, max(hi, max(pos.values())) + 0.08 * (hi - lo) + 0.3)
    ax.set_xlim(-0.2, 1.3)
    ax.set_xticks([0, 1]); ax.set_xticklabels([l, r])
    ax.set_title(tit, fontsize=9)
    despinar(ax)
axs[0].set_ylabel("F1 estricto con tipo (%)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "p2-subconjuntos.pdf"))
