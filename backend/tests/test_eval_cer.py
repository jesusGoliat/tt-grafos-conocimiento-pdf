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
