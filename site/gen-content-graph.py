"""Generate the content graph: the single machine-readable map of every chapter.

The graph is what a rename goes through instead of 500 hand-edited links. It
holds the canonical order of every published chapter plus a `renames` table
(old path -> new path). `sync-docs.py` reads order from the graph and resolves
every internal link through the rename table, so renaming a chapter is a
one-entry data change and stale references keep resolving until they are
edited. `tests/test_content_graph.py` fails if a link resolves to neither a
real file nor a rename target.

The graph is generated from the repository tree (stage order comes from the
numeric directory prefix, sub-chapter order from `curriculum-order.txt`) and
then committed. Editing it by hand is expected: the generator is the initial
snapshot, the file is the source of truth.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER_FILE = ROOT / "reference" / "standards" / "curriculum-order.txt"
GRAPH_FILE = ROOT / "reference" / "standards" / "content-graph.json"
REDIRECTS_FILE = ROOT / "site" / "route-redirects.json"

SECTIONS = [
    "01-language-model",
    "02-personalized-discovery",
    "03-quantitative-research",
    "04-agentic-platform",
    "05-game-ai",
    "07-multimodal-generation",
    "08-bio-pharma-modeling",
    "09-autonomous-driving",
    "foundations",
    "reference",
]

UNLISTED_DIRS = {"runs", "core", "prod", "cache", "data", "fixtures"}
DIR_NUM_RE = re.compile(r"^(\d+)[-_]")
DEFAULT_POSITION = 50


def chapter_order() -> dict[str, int]:
    order: dict[str, int] = {}
    if ORDER_FILE.exists():
        for line in ORDER_FILE.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                order[line] = len(order) + 1
    return order


def title_of(path: Path) -> str:
    try:
        body = path.read_text()
    except OSError:
        return ""
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return m.group(1).strip().replace("`", "") if m else ""


def sync_route_redirects(graph: dict) -> None:
    """Keep the site's redirect table in step with the graph's rename table.

    `route-redirects.json` is the historical record of moved trees (the removed
    missions/ and infra/ levels, the old platform/ and capabilities/ routes).
    It stays hand-edited for history, but the graph's `renames` now feed it too:
    every rename becomes a legacy prefix pair, and the `to` of every existing
    entry is mapped through the renames so a redirect cannot start pointing at
    nothing after a chapter is renamed.
    """
    data = json.loads(REDIRECTS_FILE.read_text())
    renames = graph.get("renames", {})

    def map_path(p: str) -> str:
        if p == "/":
            return p
        trailing = p.endswith("/")
        body = p.strip("/")
        for old in sorted(renames, key=len, reverse=True):
            if body == old or body.startswith(old + "/"):
                mapped = renames[old] + body[len(old):]
                break
        else:
            mapped = body
        # Routes follow the target's shape: a directory keeps its trailing
        # slash, a loose page (e.g. a LANDSCAPE file) does not. Normalising
        # here keeps the exact redirects in the same form the plugin's own
        # generated redirects use, so the two never fight over trailing
        # slashes.
        if (ROOT / mapped).is_dir():
            return "/" + mapped + "/"
        if (ROOT / f"{mapped}.md").is_file() or (ROOT / f"{mapped}.mdx").is_file():
            return "/" + mapped
        return "/" + mapped + ("/" if trailing else "")

    for entry in data.get("redirects", []):
        entry["to"] = map_path(entry["to"])
    legacy = data.setdefault("legacyPrefixes", [])
    existing = {(e["from"], e["to"]) for e in legacy}
    for old, new in renames.items():
        pair = (f"/{old}", f"/{new}")
        if pair not in existing:
            legacy.append({"from": pair[0], "to": pair[1]})
    REDIRECTS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    print(
        f"route-redirects.json: {len(data['redirects'])} redirects, "
        f"{len(legacy)} legacy prefixes"
    )


def main() -> None:
    order = chapter_order()
    chapters: list[dict] = []
    seen: set[str] = set()

    def add(path: str, kind: str, order_no: int) -> None:
        if path in seen:
            return
        seen.add(path)
        title = ""
        p = ROOT / path
        readme = p / "README.md" if (p / "README.md").is_file() else p
        if readme.is_file() and readme.suffix == ".md":
            title = title_of(readme)
        chapters.append(
            {"path": path, "kind": kind, "order": order_no, "title": title}
        )

    for i, section in enumerate(SECTIONS):
        add(section, "section", (i + 1) * 10)
        section_dir = ROOT / section
        if not section_dir.is_dir():
            continue

        # A stage is a numbered chapter directory whose parent is either the
        # section itself or a non-numbered surface directory (02's
        # shared/search/recommendation/ads). Its order is its numeric prefix,
        # which is the current sidebar convention and stable because it is
        # also the URL.
        def parent_is_stage(path: Path) -> bool:
            return (
                bool(DIR_NUM_RE.match(path.parent.name))
                and path.parent.name not in SECTIONS
            )

        stage_dirs = [
            p
            for p in sorted(section_dir.rglob("*/README.md"))
            if DIR_NUM_RE.match(p.parent.name)
            and not parent_is_stage(p.parent)
            and not set(p.relative_to(section_dir).parts[:-1]) & UNLISTED_DIRS
        ]
        for stage in stage_dirs:
            stage_dir = stage.parent
            stage_path = stage_dir.relative_to(ROOT).as_posix()
            stage_pos = int(DIR_NUM_RE.match(stage_dir.name).group(1))
            add(stage_path, "stage", stage_pos)
            for sub in sorted(stage_dir.iterdir()):
                if not sub.is_dir() or sub.name in UNLISTED_DIRS:
                    continue
                if not (sub / "README.md").is_file():
                    continue
                sub_path = f"{stage_path}/{sub.name}"
                add(sub_path, "sub", order.get(sub_path, DEFAULT_POSITION))

        # Everything else that is published: lineage and landscape pages,
        # overview READMEs (02's surface dirs, 07's voice/video), and detours
        # nested deeper than one level under a stage (foundations' machine
        # chapters). They keep the current default sidebar position.
        pages: list[tuple[str, int, str]] = []
        for p in sorted(section_dir.rglob("*")):
            if set(p.relative_to(section_dir).parts) & UNLISTED_DIRS:
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel in seen:
                continue
            if p.is_dir() and (p / "README.md").is_file():
                name = p.name
                title = title_of(p / "README.md")
            elif p.suffix == ".md" and p.name != "README.md":
                name = p.stem
                title = title_of(p)
            else:
                continue
            m = DIR_NUM_RE.match(name)
            if m:
                pos = int(m.group(1))
            else:
                pos = order.get(rel, DEFAULT_POSITION)
            pages.append((rel if p.is_dir() else rel[:-3], pos, title))
        pages.sort(key=lambda t: (t[1], t[2].lower()))
        for path, pos, _ in pages:
            add(path, "page", pos)

    previous = {}
    if GRAPH_FILE.exists():
        try:
            previous = json.loads(GRAPH_FILE.read_text())
        except json.JSONDecodeError:
            previous = {}
    graph = {
        "generated": "2026-08-10",
        "chapters": sorted(chapters, key=lambda c: (c["order"], c["path"])),
        # The rename table is the graph's memory of old paths. A fresh snapshot
        # of the tree must not forget it: stale references in source files keep
        # resolving through renames until they are edited.
        "renames": previous.get("renames", {}),
    }
    GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {GRAPH_FILE} with {len(chapters)} chapters")
    write_curriculum_projection(graph)
    sync_route_redirects(graph)


def write_curriculum_projection(graph: dict) -> None:
    """Rewrite `curriculum-order.txt` as the graph's human-readable projection.

    The file used to be the single source of chapter order; the graph is now.
    Regenerating it from the graph keeps the file truthful without a second
    order source to drift.
    """
    ORDER_FILE.write_text(curriculum_projection_text(graph))
    print(f"wrote {ORDER_FILE}")


def curriculum_projection_text(graph: dict) -> str:
    header = (
        "# Curriculum order — generated from reference/standards/content-graph.json.\n"
        "# Chapter order lives in the graph; this file is its readable projection.\n"
        "# One path per line, in reading order, relative to the repository root.\n"
        "# Edit the graph (or regenerate it), not this file.\n"
    )
    paths: list[str] = []
    for section in SECTIONS:
        entries = [
            c
            for c in graph["chapters"]
            if c["path"] == section or c["path"].startswith(section + "/")
        ]
        entries.sort(key=lambda c: (c["order"], c["path"]))
        paths.extend(c["path"] for c in entries)
    return header + "\n" + "\n".join(paths) + "\n"


if __name__ == "__main__":
    import sys

    if "--redirects-only" in sys.argv:
        sync_route_redirects(json.loads(GRAPH_FILE.read_text()))
    else:
        main()
