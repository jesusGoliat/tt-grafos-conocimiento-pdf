"""Escribe run_manifest.json con la configuración y el estado de una ejecución.

Uso:
    ODB_SHA256=<hash> python3 make_manifest.py <run_dir>
"""
import csv
import datetime
import json
import os
import sys
from pathlib import Path

BACKEND = Path(os.environ.get(
    "TFM_BACKEND",
    "/home/jesus/Desktop/Protocolo/Documentacion/Reporte_tecnico_plantilla/Avances_Proto/backend",
))
sys.path.insert(0, str(BACKEND))
from app.core.config import Settings

run = Path(sys.argv[1])
sample = json.loads((run / "sample.json").read_text(encoding="utf-8"))
settings = Settings()

sources = {}
final_csv = run / "cer_results.csv"
if final_csv.is_file():
    sources = {r["id"]: r["source"] for r in csv.DictReader(open(final_csv))}
results = {
    m["id"]: ("new" if sources.get(m["id"]) == "new" else
              "legacy_reused" if sources.get(m["id"]) == "legacy" else "missing")
    for m in sample
}

manifest = {
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "mineru_model_version": settings.mineru_model_version,
    "mineru_language": settings.mineru_language,
    "enable_table": settings.mineru_enable_table,
    "enable_formula": settings.mineru_enable_formula,
    "is_ocr": settings.mineru_is_ocr,
    "n_pages": len(sample),
    "n_new": sum(v == "new" for v in results.values()),
    "n_legacy_reused": sum(v == "legacy_reused" for v in results.values()),
    "ids": [m["id"] for m in sample],
    "results": results,
    "omnidocbench_sha256": os.environ.get("ODB_SHA256", ""),
}
(run / "run_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"manifiesto escrito en {run / 'run_manifest.json'} "
      f"({manifest['n_new']} nuevas, {manifest['n_legacy_reused']} heredadas, "
      f"{len(sample)} páginas)")
