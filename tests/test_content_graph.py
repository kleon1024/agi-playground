"""The content graph is the single machine-readable map of every chapter.

It exists because a rename must not mean editing five hundred hand-written
links. Order comes from the graph, and every internal link is resolved through
the graph's `renames` table at sync time; these tests make that contract hold:

1. the graph lists every published chapter, and every entry exists;
2. the graph agrees with the human-readable `curriculum-order.txt` projection;
3. every internal link in every published page resolves -- through renames --
   to a real file, a real directory, or a chapter the graph knows about.
"""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC_DOCS_PATH = ROOT / "site" / "sync-docs.py"

SPEC = importlib.util.spec_from_file_location("sync_docs", SYNC_DOCS_PATH)
assert SPEC is not None and SPEC.loader is not None
SYNC_DOCS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC_DOCS)

SECTIONS = [
    name for name, _ in SYNC_DOCS.SECTIONS
]


def published_pages():
    for section in SECTIONS:
        for page in sorted((ROOT / section).rglob("*.md")):
            if {"core", "prod", "runs", "cache"} & set(page.parts):
                continue
            yield page


def chapter_of(page: Path) -> str:
    if page.name == "README.md":
        return page.parent.relative_to(ROOT).as_posix()
    return page.relative_to(ROOT).with_suffix("").as_posix()


def test_graph_lists_every_published_chapter():
    graph = SYNC_DOCS.GRAPH_BY_PATH
    missing = []
    for page in published_pages():
        chapter = chapter_of(page)
        if chapter not in graph:
            missing.append(chapter)
    assert not missing, (
        "published but missing from reference/standards/content-graph.json; "
        "regenerate it with `uv run python site/gen-content-graph.py`:\n  "
        + "\n  ".join(missing)
    )
    stale = []
    for chapter, entry in graph.items():
        if entry.get("kind") == "section":
            probe = ROOT / chapter / "README.md"
        else:
            probe = ROOT / chapter
            if not probe.is_dir():
                probe = ROOT / (chapter + ".md")
        if not probe.exists():
            stale.append(chapter)
    assert not stale, "content-graph.json points at paths that do not exist:\n  " + (
        "\n  ".join(stale)
    )


def test_graph_agrees_with_the_curriculum_projection():
    """`curriculum-order.txt` is the human-readable projection of the graph.

    Both carry an order for the same paths; where they overlap they must agree,
    so a hand edit to either file is caught instead of silently winning.
    """
    if not SYNC_DOCS.ORDER_FILE.exists():
        return
    file_order = {}
    for line in SYNC_DOCS.ORDER_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            file_order[line] = len(file_order) + 1
    disagreements = []
    for path, pos in file_order.items():
        entry = SYNC_DOCS.GRAPH_BY_PATH.get(path)
        if (
            entry is not None
            and entry.get("kind") != "section"
            and entry["order"] != pos
        ):
            disagreements.append(f"{path}: file={pos} graph={entry['order']}")
    assert not disagreements, (
        "curriculum-order.txt and content-graph.json disagree on order:\n  "
        + "\n  ".join(disagreements)
    )


def test_renames_values_resolve():
    """A rename target must exist (or be a graph chapter) after the rename."""
    problems = []
    for old, new in SYNC_DOCS.RENAMES.items():
        if not (ROOT / new).exists() and new not in SYNC_DOCS.GRAPH_BY_PATH:
            problems.append(f"{old} -> {new}")
    assert not problems, "rename targets that resolve nowhere:\n  " + "\n  ".join(problems)


def test_every_internal_link_resolves_through_the_graph():
    """The point of the graph: a rename must not break the site's links.

    Every internal link in every published page is resolved against the source
    file, mapped through the graph's rename table, and must then point at a
    real file or directory or a chapter the graph knows. A link that resolves
    to neither is a broken link that Docusaurus would only find at build time,
    after the rename has already touched hundreds of files by hand.
    """
    link_re = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")
    broken = []
    for page in published_pages():
        src_rel = page.relative_to(ROOT)
        for match in link_re.finditer(page.read_text()):
            target = match.group(3)
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            target = target.split("#", 1)[0]
            target = target.rstrip("/")
            if not target:
                continue
            resolved = (ROOT / src_rel.parent / target).resolve()
            try:
                resolved = resolved.relative_to(ROOT)
            except ValueError:
                continue
            mapped = Path(SYNC_DOCS.apply_renames(resolved.as_posix()))
            exists = (
                mapped.exists()
                or mapped.as_posix() in SYNC_DOCS.GRAPH_BY_PATH
                or (ROOT / resolved.as_posix()).exists()
            )
            if not exists:
                broken.append(
                    f"{src_rel.as_posix()}: [{match.group(2)}]({match.group(3)}) "
                    f"-> {resolved.as_posix()} (renamed: {mapped.as_posix()})"
                )
    assert not broken, (
        "internal links that resolve to neither a file nor a graph chapter; "
        "add a `renames` entry or fix the link:\n  " + "\n  ".join(broken[:40])
    )
