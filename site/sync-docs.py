#!/usr/bin/env python3
"""Generate the docs site's pages from the repository's markdown.

There is exactly one copy of every lesson, and it lives in the repository. This
script mirrors that markdown into `site/docs/` at build time, so the site can
never drift from the source. Nothing under `site/docs/` is hand-edited, and it
is git-ignored to make that impossible to forget.

The mirroring preserves directory structure and renames `README.md` to
`index.md`. Source links remain relative for GitHub, while generated-page links
are rewritten to absolute site routes because Docusaurus resolves a directory
index from its parent route when `trailingSlash` is disabled. Three things need
translating:

* links to source files (`.py`, `.yaml`, `.json`), which have no page on the
  site, become links to the file on GitHub;
* links to lessons and other markdown pages become `/playground/...` routes;
* images are copied alongside their page.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "docs"
REPO = "https://github.com/kleon1024/agi-playground/blob/main"
BASE_URL = "/playground"

# Directories mirrored into the site, in sidebar order.
SECTIONS = [
    ("foundations", 20),
    ("platform", 30),
    ("capabilities", 40),
    ("missions", 50),
    ("standards", 60),
    ("infra", 70),
    ("research", 80),
]

CODE_SUFFIXES = (".py", ".yaml", ".yml", ".json", ".toml", ".sh", ".txt")
ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")

# A lesson opts into an interactive widget with an HTML comment, which GitHub
# renders as nothing and the site turns into a live component. That keeps the
# repository markdown the single source without it having to know about React.
INTERACTIVE_RE = re.compile(
    r"^<!--\s*interactive:\s*(\w+)\s*-->\s*$",
    re.MULTILINE,
)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

TITLE_OVERRIDES = {
    "foundations": "Foundations",
    "platform": "Platform",
    "capabilities": "Capabilities",
    "missions": "Missions",
    "standards": "Standards",
    "infra": "Infrastructure",
    "research": "Research",
}

# Directories that hold supporting material rather than a lesson. Without these
# the sidebar shows a bare lowercase "runs" or "prod" beside real chapters.
# The positions push them below the lesson content they support.
DIR_OVERRIDES = {
    "runs": ("Evidence", 80),
    "core": ("Core implementation", 95),
    "prod": ("Production notes", 96),
}

# Reference tables sit beside the lesson they annotate. Their H1s repeat the
# chapter name ("03 — Pretraining: Landscape"), which reads as a second chapter
# in the sidebar, so the nav label is shortened and pushed after the evidence.
FILE_OVERRIDES = {"LANDSCAPE.md": ("Landscape", 90)}

# Chapter order comes from one file, never from the headings. See the comment
# at the top of that file for why. Sub-lessons inside a chapter still sort by
# their directory's numeric prefix (`01-distributed`), which is stable because
# it is also the URL.
ORDER_FILE = ROOT / "standards" / "curriculum-order.txt"
DIR_NUM_RE = re.compile(r"^(\d+)[-_]")
DEFAULT_POSITION = 50


def load_chapter_order() -> dict[str, int]:
    """Read the curriculum spine into `path -> 1-based position`."""
    if not ORDER_FILE.exists():
        return {}
    order: dict[str, int] = {}
    for line in ORDER_FILE.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            order[line] = len(order) + 1
    return order


CHAPTER_ORDER = load_chapter_order()


def title_from(path: Path, body: str) -> str:
    """Prefer the document's own H1; fall back to a tidied directory name."""
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if m:
        return m.group(1).strip().replace("`", "")
    name = path.parent.name if path.name == "README.md" else path.stem
    return name.replace("-", " ").replace("_", " ").title()


def chapter_of(path: Path) -> int | None:
    """The curriculum position of the chapter a file belongs to, if any."""
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    for parent in [rel, *rel.parents]:
        position = CHAPTER_ORDER.get(parent.as_posix())
        if position is not None:
            return position
    return None


def order_from(path: Path) -> int:
    """Sidebar position for one page.

    A chapter takes its number from the curriculum spine. Anything below a
    chapter sorts by its directory's numeric prefix, which is stable because
    renaming it is a real URL change rather than a silent renumbering.
    """
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    if rel.name == "README.md":
        position = CHAPTER_ORDER.get(rel.parent.as_posix())
        if position is not None:
            return position
    name = rel.parent.name if rel.name == "README.md" else rel.stem
    m = DIR_NUM_RE.match(name)
    if m:
        return int(m.group(1))
    return DEFAULT_POSITION


def numbered(title: str, path: Path) -> str:
    """Compose the displayed title: the chapter number plus the heading.

    The number is generated here so that no heading has to carry it, which is
    what makes inserting a chapter a one-line change.
    """
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    if rel.name != "README.md":
        return title
    position = CHAPTER_ORDER.get(rel.parent.as_posix())
    return f"{position:02d} — {title}" if position else title


def rewrite_links(text: str, src_rel: Path) -> str:
    """Point source files at GitHub and lesson links at their public routes."""

    def repl(m: re.Match) -> str:
        bang, label, target = m.groups()
        if target.startswith(("http://", "https://", "#", "mailto:", "/")):
            return m.group(0)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if not target:
            return m.group(0)
        if bang:  # image — resolved by the copy step below
            return m.group(0)
        if target.endswith(CODE_SUFFIXES + ASSET_SUFFIXES):
            resolved = (ROOT / src_rel.parent / target).resolve().relative_to(ROOT)
            return f"[{label}]({REPO}/{resolved.as_posix()}{anchor})"
        # A bare `runs/` directory has no page — only the files inside it do.
        # Point those at GitHub, where the directory listing exists.
        if target.rstrip("/").endswith("runs"):
            resolved = (ROOT / src_rel.parent / target).resolve().relative_to(ROOT)
            return f"[{label}]({REPO.replace('/blob/', '/tree/')}/{resolved.as_posix()}{anchor})"
        resolved = (ROOT / src_rel.parent / target).resolve().relative_to(ROOT)
        if resolved.name == "README.md":
            resolved = resolved.parent
        elif resolved.suffix == ".md":
            resolved = resolved.with_suffix("")
        route = BASE_URL
        if resolved.as_posix() not in ("", "."):
            route += f"/{resolved.as_posix()}"
        return f"[{label}]({route}{anchor})"

    return LINK_RE.sub(repl, text)


def fix_admonition_titles(text: str) -> str:
    """Rewrite `:::note Title` to `:::note[Title]`.

    MDX 3 uses directive-label syntax for admonition titles. The older
    `:::note Title` form does not error — it silently degrades to a literal
    paragraph reading ":::note Title", which is easy to miss in review and
    looks broken to every reader.
    """
    return re.sub(
        r"^:::(tip|note|info|warning|danger|caution)[ \t]+(?!\[)(.+?)[ \t]*$",
        lambda m: f":::{m.group(1)}[{m.group(2)}]",
        text,
        flags=re.MULTILINE,
    )


def escape_mdx(text: str) -> str:
    """Escape characters MDX would read as JSX, outside code fences.

    MDX 3 treats `<` as the start of a JSX tag, so prose like "under <1,000
    lines" or "<UNK>" fails to compile. Inside fenced code blocks these must be
    left exactly as written, so fences are stepped over rather than rewritten.
    """
    out, in_fence = [], False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # A `<` that is not opening a tag or a closing tag is literal text.
        out.append(re.sub(r"<(?![a-zA-Z/!])", "&lt;", line))
    return "\n".join(out)


def description_from(body: str) -> str:
    """First real sentence of prose, for the meta description.

    This is what search results display under the title, so it should read as a
    summary rather than as whatever markup happened to come first. Headings,
    blockquotes, code fences, tables and images are skipped.
    """
    skip_prefixes = ("#", ">", "```", "|", "---", "!", "<", ":::", "*", "-")
    for para in re.split(r"\n\s*\n", body):
        line = " ".join(para.split())
        if not line or line.startswith(skip_prefixes):
            continue
        # Strip inline markup that would look wrong in a search snippet.
        line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"[*_`$]", "", line)
        if len(line) < 40:
            continue
        if len(line) > 155:
            cut = line[:155].rsplit(" ", 1)[0]
            return cut + "…"
        return line
    return ""


def convert(src: Path, dest: Path, position: int | None) -> tuple[str, int]:
    body = src.read_text()
    src_rel = src.relative_to(ROOT)

    existing = FRONTMATTER_RE.match(body)
    meta: dict[str, str] = {}
    if existing:
        for line in existing.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = body[existing.end():]

    body = rewrite_links(body, src_rel)
    body = escape_mdx(body)
    body = fix_admonition_titles(body)

    # The meta description is what a search result shows under the title, so it
    # has to come from the prose. Take it before widget imports are prepended:
    # an import statement is longer than the 40-character floor and starts with
    # no skipped prefix, so every interactive page otherwise advertised
    # "import KVCacheGrowth from '@site/src/components/KVCacheGrowth';".
    desc = description_from(body).replace('"', "'")

    widgets = sorted(set(INTERACTIVE_RE.findall(body)))
    if widgets:
        body = INTERACTIVE_RE.sub(lambda m: f"<{m.group(1)} />", body)
        imports = "\n".join(
            f"import {w} from '@site/src/components/{w}';" for w in widgets
        )
        body = f"\n{imports}\n{body}"
        dest = dest.with_suffix(".mdx")

    # Docusaurus needs the H1 removed when a title is supplied, or the page
    # shows it twice.
    title = meta.get("title") or title_from(src, body)
    body = re.sub(r"^#\s+.+\n", "", body, count=1, flags=re.MULTILINE)

    label, override_pos = FILE_OVERRIDES.get(src.name, (None, None))
    if position is None:
        position = override_pos if override_pos is not None else order_from(src)
    title = numbered(title, src)

    lines = ["---", f'title: "{title}"']
    if desc:
        lines.append(f'description: "{desc}"')
    lines.append(f"sidebar_position: {position}")
    status = meta.get("status")
    if label:
        lines.append(f'sidebar_label: "{label}"')
    elif status:
        # Surface build status in the sidebar rather than hiding it in prose.
        suffix = " — verified" if status == "verified" else ""
        lines.append(f'sidebar_label: "{title}{suffix}"')
    lines.append("---")
    lines.append("")
    # A bare filename means nothing to a reader on the web. Link the source
    # instead of naming it.
    lines.append(f"[View source on GitHub]({REPO}/{src_rel.as_posix()})")
    lines.append("")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + body)
    return title, position


def write_category_files(section: str, dir_meta: dict[Path, tuple[str, int]]) -> None:
    """Give every generated directory an explicit sidebar label and position.

    Without a `_category_.json`, Docusaurus labels a category with its raw
    directory name and sorts it alphabetically — which is how a curriculum
    numbered 02, 03, 04, 06, 07 came to display in the order 02, 07, 06, 03
    with a lowercase "adaptation" in the middle of it.
    """
    for path in sorted((OUT / section).rglob("*")):
        if not path.is_dir():
            continue
        rel = path.relative_to(OUT)
        name = path.name
        if name in DIR_OVERRIDES:
            label, position = DIR_OVERRIDES[name]
        elif rel in dir_meta:
            label, position = dir_meta[rel]
        else:
            # An intermediate directory with no lesson of its own, such as
            # `platform/adaptation/`. Name it from the directory and sort it
            # with the chapters it contains.
            label = name.replace("-", " ").replace("_", " ").capitalize()
            nested = [
                pos for child, (_, pos) in dir_meta.items()
                if child.is_relative_to(rel)
            ]
            position = min(nested) if nested else DEFAULT_POSITION
        payload = f'{{"label": "{label}", "position": {position}}}\n'
        (path / "_category_.json").write_text(payload)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Landing page is maintained by hand — it carries the interactive demo.
    landing = Path(__file__).resolve().parent / "landing.mdx"
    if landing.exists():
        shutil.copy(landing, OUT / "index.mdx")

    count = 0
    for section, base_pos in SECTIONS:
        src_dir = ROOT / section
        if not src_dir.is_dir():
            continue
        (OUT / section).mkdir(parents=True, exist_ok=True)
        (OUT / section / "_category_.json").write_text(
            f'{{"label": "{TITLE_OVERRIDES[section]}", "position": {base_pos}}}\n'
        )
        # A directory becomes a sidebar category. Remember what each one is
        # called and where it sorts, so the category can be labelled from the
        # lesson's own H1 instead of its directory name.
        dir_meta: dict[Path, tuple[str, int]] = {}
        for src in sorted(src_dir.rglob("*.md")):
            rel = src.relative_to(ROOT)
            dest_rel = rel.with_name("index.md") if src.name == "README.md" else rel
            title, position = convert(src, OUT / dest_rel, None)
            if src.name == "README.md" and rel.parent != Path(section):
                dir_meta[rel.parent] = (title, position)
            count += 1

        # Section roots are linked to as directories (e.g. ../../platform/) but
        # have no README of their own, so give them a landing page.
        if not (src_dir / "README.md").exists():
            children = sorted(
                (dir_meta.get(Path(section) / d.name, (d.name, DEFAULT_POSITION)), d.name)
                for d in src_dir.iterdir()
                if d.is_dir() and (d / "README.md").exists()
            )
            listing = "\n".join(
                f"- [{meta[0]}]({name}/)" for meta, name in sorted(children)
            )
            (OUT / section / "index.md").write_text(
                f'---\ntitle: "{TITLE_OVERRIDES[section]}"\n---\n\n{listing}\n'
            )

        write_category_files(section, dir_meta)

        # Images and charts referenced by those pages.
        for img in sorted(src_dir.rglob("*.png")):
            rel = img.relative_to(ROOT)
            (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, OUT / rel)

    print(f"synced {count} pages from the repository into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
