#!/usr/bin/env python3
"""Generate the docs site's pages from the repository's markdown.

There is exactly one copy of every lesson, and it lives in the repository. This
script mirrors that markdown into `site/docs/` at build time, so the site can
never drift from the source. Nothing under `site/docs/` is hand-edited, and it
is git-ignored to make that impossible to forget.

The mirroring preserves directory structure and renames `README.md` to
`index.md`, which means the relative links already written for GitHub keep
resolving on the site without rewriting — `../../platform/training/` points at
the same place in both trees. Only two things need translating:

* links to source files (`.py`, `.yaml`, `.json`), which have no page on the
  site, become links to the file on GitHub;
* images are copied alongside their page.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "docs"
REPO = "https://github.com/kleon1024/agi-playground/blob/main"

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
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")

# A lesson opts into an interactive widget with an HTML comment, which GitHub
# renders as nothing and the site turns into a live component. That keeps the
# repository markdown the single source without it having to know about React.
INTERACTIVE_RE = re.compile(r"^<!--\s*interactive:\s*(\w+)\s*-->\s*$", re.M)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)

TITLE_OVERRIDES = {
    "foundations": "Foundations",
    "platform": "Platform",
    "capabilities": "Capabilities",
    "missions": "Missions",
    "standards": "Standards",
    "infra": "Infrastructure",
    "research": "Research",
}


def title_from(path: Path, body: str) -> str:
    """Prefer the document's own H1; fall back to a tidied directory name."""
    m = re.search(r"^#\s+(.+)$", body, re.M)
    if m:
        return m.group(1).strip().replace("`", "")
    name = path.parent.name if path.name == "README.md" else path.stem
    return name.replace("-", " ").replace("_", " ").title()


def rewrite_links(text: str, src_rel: Path) -> str:
    """Point code links at GitHub; leave page links alone."""

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
        if target.endswith(CODE_SUFFIXES):
            resolved = (src_rel.parent / target).resolve().relative_to(ROOT)
            return f"[{label}]({REPO}/{resolved.as_posix()}{anchor})"
        # `README.md` is `index.md` on the site, so a link that names the file
        # explicitly must drop it or it 404s.
        if target.endswith("README.md"):
            target = target[: -len("README.md")] or "./"
            return f"[{label}]({target}{anchor})"
        # A bare `runs/` directory has no page — only the files inside it do.
        # Point those at GitHub, where the directory listing exists.
        if target.rstrip("/").endswith("runs"):
            resolved = (src_rel.parent / target).resolve().relative_to(ROOT)
            return f"[{label}]({REPO.replace('/blob/', '/tree/')}/{resolved.as_posix()}{anchor})"
        return m.group(0)

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
        flags=re.M,
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
        if stripped.startswith("```") or stripped.startswith("~~~"):
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


def convert(src: Path, dest: Path, position: int | None) -> None:
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
    body = re.sub(r"^#\s+.+\n", "", body, count=1, flags=re.M)

    desc = description_from(body).replace('"', "'")
    lines = ["---", f'title: "{title}"']
    if desc:
        lines.append(f'description: "{desc}"')
    if position is not None:
        lines.append(f"sidebar_position: {position}")
    status = meta.get("status")
    if status:
        # Surface build status in the sidebar rather than hiding it in prose.
        lines.append(f'sidebar_label: "{title}{" ✅" if status == "verified" else ""}"')
    lines.append("---")
    lines.append("")
    # A bare filename means nothing to a reader on the web. Link the source
    # instead of naming it.
    lines.append(f"[View source on GitHub]({REPO}/{src_rel.as_posix()})")
    lines.append("")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + body)
    return widgets


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
        # Section roots are linked to as directories (e.g. ../../platform/) but
        # have no README of their own, so give them a landing page.
        if not (src_dir / "README.md").exists():
            children = sorted(
                d.name for d in src_dir.iterdir()
                if d.is_dir() and (d / "README.md").exists()
            )
            listing = "\n".join(f"- [{c.replace('-', ' ')}]({c}/)" for c in children)
            (OUT / section / "index.md").write_text(
                f'---\ntitle: "{TITLE_OVERRIDES[section]}"\n---\n\n{listing}\n'
            )
        for src in sorted(src_dir.rglob("*.md")):
            rel = src.relative_to(ROOT)
            dest_rel = rel.with_name("index.md") if src.name == "README.md" else rel
            convert(src, OUT / dest_rel, None)
            count += 1
        # Images and charts referenced by those pages.
        for img in sorted(src_dir.rglob("*.png")):
            rel = img.relative_to(ROOT)
            (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, OUT / rel)

    print(f"synced {count} pages from the repository into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
