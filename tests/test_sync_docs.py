import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC_DOCS_PATH = ROOT / "site" / "sync-docs.py"

SPEC = importlib.util.spec_from_file_location("sync_docs", SYNC_DOCS_PATH)
assert SPEC is not None and SPEC.loader is not None
SYNC_DOCS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC_DOCS)


def test_relative_lesson_links_become_absolute_public_routes():
    source = Path("foundations/README.md")
    markdown = (
        "[loop](01-first-training-loop/) "
        "[training](../platform/training/README.md#next)"
    )

    rewritten = SYNC_DOCS.rewrite_links(markdown, source)

    assert "[loop](/playground/foundations/01-first-training-loop)" in rewritten
    assert "[training](/playground/platform/training#next)" in rewritten


def test_relative_source_links_stay_on_github():
    source = Path("missions/01-language-model-agent/01-tokenizer/README.md")
    markdown = "[implementation](core/bpe.py)"

    rewritten = SYNC_DOCS.rewrite_links(markdown, source)

    assert rewritten == (
        "[implementation](https://github.com/kleon1024/agi-playground/blob/main/"
        "missions/01-language-model-agent/01-tokenizer/core/bpe.py)"
    )
