import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("eval_cer", Path(__file__).parents[1] / "scripts" / "eval_cer.py")
eval_cer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_cer)


def test_cer_identical_after_normalization():
    assert eval_cer.cer(eval_cer.normalize("# Hola  **mundo**"), eval_cer.normalize("Hola mundo")) == 0


def test_cer_counts_edits():
    assert eval_cer.cer("gato", "pato") == 0.25
    assert eval_cer.levenshtein("", "abc") == 3


def test_blocks_text_includes_lists_and_captions_excludes_tables():
    blocks = [
        {"type": "text", "text": "Cuerpo", "text_level": 1},
        {"type": "list", "list_items": ["uno", "dos"]},
        {"type": "table", "table_body": "<table>x</table>", "table_caption": ["Tabla 1"],
         "table_footnote": ["Nota"]},
        {"type": "image", "image_caption": ["Figura 1"]},
        {"type": "chart", "chart_caption": ["Gráfico 1"], "chart_footnote": ["Fuente"]},
        {"type": "page_number", "text": "7"},
        {"type": "footer", "text": "pie"},
        {"type": "equation", "text": "x^2"},
    ]
    assert (eval_cer.blocks_text(blocks)
            == "Cuerpo\nuno\ndos\nTabla 1\nNota\nFigura 1\nGráfico 1\nFuente")


def test_normalize_does_not_remove_latex_commands():
    # La normalización quita \, _ y $, pero conserva letras y llaves de LaTeX.
    assert eval_cer.normalize(r"$\alpha_{1}$ + x^2") == "alpha {1} + x^2"
