"""Descarga las imágenes de la muestra, las convierte a PDF de una página y las extrae con el MinerUApiExtractor del backend."""
import asyncio, datetime, json, os, sys, urllib.parse, urllib.request
from pathlib import Path
# El backend se localiza a partir de la ubicación del script; TFM_BACKEND permite
# apuntar a otra copia.
BACKEND = Path(os.environ.get("TFM_BACKEND") or Path(__file__).resolve().parents[2])
if not (BACKEND / "app").is_dir():
    raise SystemExit(f"No se encontró el backend en {BACKEND}; define TFM_BACKEND.")
sys.path.insert(0, str(BACKEND))
import pymupdf
from app.core.config import Settings
from app.services.mineru_client import MinerUClient
from app.services.extraction import MinerUApiExtractor

run = Path(sys.argv[1]); only = int(sys.argv[2]) if len(sys.argv) > 2 else None
meta = json.loads((run / "sample.json").read_text())[:only]
HF = "https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/main/images/"

def to_pdf(img: Path, pdf: Path):
    with pymupdf.open(img) as im:
        pdf.write_bytes(im.convert_to_pdf())

CONCURRENCY = int(os.environ.get("MINERU_CONCURRENCY", "4"))
RETRIES = int(os.environ.get("MINERU_RETRIES", "3"))

async def main():
    settings = Settings()
    client = MinerUClient(settings)
    ext = MinerUApiExtractor(client, settings)
    sem = asyncio.Semaphore(CONCURRENCY)

    async def one(i, m):
        out = run / "results" / m["id"]
        if (out / "content_list.json").exists():
            return m["id"], "cached"
        img = run / "images" / m["image"]; img.parent.mkdir(parents=True, exist_ok=True)
        pdf = run / "pdfs" / f"odb_{i:02d}.pdf"; pdf.parent.mkdir(parents=True, exist_ok=True)
        last = None
        for attempt in range(RETRIES):
            try:
                if not img.exists():
                    urllib.request.urlretrieve(HF + urllib.parse.quote(m["image"]), img)
                to_pdf(img, pdf)
                async with sem:
                    out.mkdir(parents=True, exist_ok=True)
                    async def prog(status, progress): pass
                    await ext.extract(pdf, pdf.name, out, prog)
                return m["id"], "done"
            except Exception as e:
                last = e
                if attempt + 1 < RETRIES:
                    await asyncio.sleep(5 * (attempt + 1))
        return m["id"], f"failed: {last}"
    res = await asyncio.gather(*(one(i, m) for i, m in enumerate(meta)))
    await client.aclose()
    for r in res: print(*r)
    manifest = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mineru_model_version": settings.mineru_model_version,
        "mineru_language": settings.mineru_language,
        "enable_table": settings.mineru_enable_table,
        "enable_formula": settings.mineru_enable_formula,
        "is_ocr": settings.mineru_is_ocr,
        "n_pages": len(meta),
        "ids": [m["id"] for m in meta],
        "results": dict(res),
        "omnidocbench_sha256": os.environ.get("ODB_SHA256", ""),
    }
    (run / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
asyncio.run(main())
