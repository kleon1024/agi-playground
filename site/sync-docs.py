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

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "docs"
REPO = "https://github.com/kleon1024/agi-playground/blob/main"
BASE_URL = "/playground"

# Directories mirrored into the site, in sidebar order.
#
# Missions come first because they are the only reader path. Everything below
# them is a support library a mission links into at the point where a decision
# needs it, not a track to be read front to back — so the sidebar must not
# present foundations, platform, and capabilities as a sequence leading up to a
# mission. Contributor surfaces sort last.
SECTIONS = [
    ("missions", 20),
    ("foundations", 30),
    ("capabilities", 40),
    ("platform", 50),
    ("infra", 60),
    ("standards", 70),
    ("research", 80),
]

# Source and raw evidence alike: anything a reader follows to look at bytes
# rather than to read a page. `runs/` entries cite their own records --
# `.jsonl` result rows, `.diff` patches -- and those are files on GitHub, not
# routes on this site. Omitting them here does not produce a wrong link, it
# produces a broken build, which is the better failure of the two.
CODE_SUFFIXES = (
    ".py", ".yaml", ".yml", ".json", ".jsonl", ".toml", ".sh", ".txt", ".diff", ".csv",
)
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

# A section root used to render as a bare bullet list, which told a reader
# arriving from a mission link nothing about what they had walked into or when
# to walk back out. Each section owns a different kind of claim, and saying so
# is what keeps these from reading as four parallel courses.
SECTION_INTROS = {
    "missions": (
        "**Missions are the reader path.** A mission starts with a stakeholder "
        "problem, carries one concrete artifact through every stage, and ends "
        "at a measured outcome with its evidence boundary stated. It links out "
        "to a foundation, capability, or platform chapter only where a decision "
        "needs one, and that chapter hands back something the next stage uses.\n\n"
        "Start here. Everything below this section exists to be linked into."
    ),
    "foundations": (
        "**Prerequisite mechanism, bound to no product.** These chapters explain "
        "mathematics and mechanics you need in order to reason about a decision "
        "a mission is about to make. They are scoped to language models, not to "
        "intelligence in general, and they are not a course to read front to "
        "back — arrive from the mission stage that sent you, and return to it."
    ),
    "capabilities": (
        "**Reusable decision primitives.** A capability is admitted only after "
        "at least two missions need the same input/output contract and the same "
        "objective. Until then the explanation stays local to the first mission "
        "that needed it, because reuse of a technique is not reuse of a "
        "decision. Every capability claim is backed by a run."
    ),
    "platform": (
        "**Cross-mission lifecycle reference.** Data, training, adaptation, "
        "serving, evaluation, and safety — the contracts and tradeoffs that "
        "recur no matter which mission you are running. Platform owns execution, "
        "never a stakeholder outcome, and these chapters are reference material "
        "rather than a linear sequence. Each one is entered from a mission "
        "decision and returns an artifact, a measurement, or a diagnostic."
    ),
    "infra": (
        "**Where the work runs.** Runbooks for the two compute lanes this "
        "repository uses, including verified setup paths and the failure modes "
        "worth knowing before you hit them. Naming specific hardware belongs "
        "here and in run records, not in curriculum prose."
    ),
    "standards": (
        "**Contributor surface, not a learner path.** The contracts every lesson, "
        "run record, and mission must satisfy before its numbers mean anything. "
        "Read these before contributing; skip them if you are here to learn."
    ),
    "research": (
        "**Dated landscape evidence.** Why the technical choices elsewhere in "
        "this repository were made, with external results attributed and dated. "
        "Reference material, consulted from a decision rather than read through."
    ),
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


# An inline code span, so its contents can be stepped over the way a fenced
# block is. Longest-run-first, because ``a `b` c`` is one span, not three.
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)*\1")


def escape_mdx(text: str) -> str:
    """Escape characters MDX would read as JSX, outside code.

    MDX 3 treats `<` as the start of a JSX tag, so prose like "under <1,000
    lines" fails to compile. Two places must be left exactly as written: fenced
    blocks, and **inline code spans**.

    A `<` followed by a letter is left alone on purpose, because it is
    genuinely ambiguous — `<Widget />` in a lesson is a component the page means
    to render. Anything tag-shaped that must appear literally goes in backticks.

    Inline code is the one that bit. MDX does not parse JSX inside a code span,
    so `<|im_start|>` in backticks compiles fine and needs no escaping — but
    escaping it anyway does not round-trip. Markdown renders a code span's
    contents literally, entities included, so `&lt;|im_start|>` reached the
    published page as those exact eight characters. The chat-template section of
    the SFT lesson shipped reading `&lt;|im_start|>user` for a week, which is
    both wrong and, in a chapter arguing that the template is a learned
    convention rather than magic syntax, wrong in the most confusing possible
    place.
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
        # A `<` that is not opening a tag or a closing tag is literal text —
        # but only outside inline code, which MDX already leaves alone.
        pieces, cursor = [], 0
        for span in INLINE_CODE_RE.finditer(line):
            pieces.append(re.sub(r"<(?![a-zA-Z/!])", "&lt;", line[cursor:span.start()]))
            pieces.append(span.group(0))
            cursor = span.end()
        pieces.append(re.sub(r"<(?![a-zA-Z/!])", "&lt;", line[cursor:]))
        out.append("".join(pieces))
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


# A few READMEs open with a "Read this online" callout, which is useful on
# GitHub — where the interactive widgets are invisible — and absurd on the site
# it points at, where it renders as a link to the page you are already reading.
# Stripped from the generated page and left in the repository file.
READ_ONLINE_RE = re.compile(r"^>\s*\*\*\[Read this online\].*?(?:\n(?!\n).*)*\n+", re.MULTILINE)


# What a reader is being asked for before they start, in the two units they
# actually budget with: how hard, and how long.
LEVEL_LABELS = {
    "foundation": "Foundation",
    "applied": "Applied",
    "frontier": "Frontier",
    "reference": "Reference",
}
WORDS_PER_MINUTE = 200  # technical prose, read rather than skimmed
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
TABLE_ROW_RE = re.compile(r"^\|.*\|$", re.MULTILINE)
PROSE_WORD_RE = re.compile(r"[A-Za-z0-9'-]+")


def reading_minutes(body: str) -> int:
    """Minutes of prose, computed rather than declared.

    Code fences and table rows are excluded: they are scanned, not read at
    prose speed, and counting them made reference-heavy pages claim twice the
    time they take. Computing this at sync time rather than writing it into
    frontmatter means the number cannot drift away from the page it describes
    -- an author who adds four paragraphs does not have to remember to update
    a figure, and one who forgets cannot publish a lie about it.
    """
    text = CODE_FENCE_RE.sub("", body)
    text = TABLE_ROW_RE.sub("", text)
    words = len(PROSE_WORD_RE.findall(text))
    return max(1, round(words / WORDS_PER_MINUTE))


def cost_suffix(dir_cost: dict[Path, tuple[str, int]], section: str, name: str) -> str:
    """What a chapter costs, shown where the reader picks one.

    A section index listing bare titles makes the reader open each entry to
    find out whether it is a twenty-minute foundation or a five-minute
    reference.
    """
    level, minutes = dir_cost.get(Path(section) / name, ("", 0))
    if level not in LEVEL_LABELS:
        return ""
    return f" — {LEVEL_LABELS[level]}, {minutes} min"


def convert(src: Path, dest: Path, position: int | None) -> tuple[str, int, str, str, int]:
    body = READ_ONLINE_RE.sub("", src.read_text())
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

    # Measured here, before widget imports are prepended: an `import ... from
    # '@site/...'` line is not prose and counting it inflates exactly the
    # interactive chapters.
    minutes = reading_minutes(body)

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

    lines = ["---", f'title: "{title}"']
    if desc:
        lines.append(f'description: "{desc}"')
    lines.append(f"sidebar_position: {position}")
    status = meta.get("status")
    nav_label = label or short_label(src, meta)
    if status == "verified" and src.name == "README.md":
        # Build status belongs where a reader chooses what to read next.
        nav_label = f"{nav_label} \u00b7 verified"
    lines.append(f'sidebar_label: "{nav_label}"')
    lines.append("---")
    lines.append("")

    # The learning contract's cheapest half: what this page assumes, and what it
    # will cost to read. 80,000 words with neither is a wall, and a reader who
    # cannot see which chapters are foundations has no way to sequence them
    # except the sidebar's order, which is a curriculum position and not a
    # difficulty.
    level = meta.get("level", "")
    if level in LEVEL_LABELS:
        lines.append(f"**{LEVEL_LABELS[level]}** · {minutes} min read")
        lines.append("")

    # Which weights a lesson's claims rest on changes how you read every number
    # on the page, and it is invisible in a loss curve. This stays at the top
    # because it conditions how the rest of the page is read. `none` is
    # omitted: a corpus or tokenizer lesson has no model to attribute anything
    # to.
    base = meta.get("base")
    if base == "scratch":
        lines.append("**Base model:** trained from scratch in this repository.")
        lines.append("")
    elif isinstance(base, str) and base.startswith("external:"):
        lines.append(f"**Base model:** the published checkpoint `{base[len('external:') :]}`.")
        lines.append("")

    # The source link goes last. It used to sit above the first paragraph,
    # where the first thing a learner met was an invitation to leave — and the
    # opening viewport is supposed to establish the learning contract, not
    # offer an exit. A reader who wants the source wants it after reading.
    footer = f"\n\n---\n\n[View source on GitHub]({REPO}/{src_rel.as_posix()})\n"

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + body.rstrip("\n") + footer)
    return title, position, nav_label, level, minutes


def short_label(path: Path, meta: dict[str, str]) -> str:
    """The nav label, which is not the page title.

    A chapter heading is a question the reader is about to answer — "What has
    to be true of text before you train on it?" — and that is right on the
    page and unusable in a sidebar, where eight of them wrap to two lines each
    and become a wall. The label is a short noun; `label:` in the frontmatter
    overrides the tidied directory name when that name is a poor one.
    """
    if meta.get("label"):
        return meta["label"]
    name = path.parent.name if path.name == "README.md" else path.stem
    name = DIR_NUM_RE.sub("", name).replace("-", " ").replace("_", " ").strip()
    return name[:1].upper() + name[1:] if name else "Overview"


# Supporting material: real pages, reachable from the prose that cites them,
# but not nodes in the curriculum. Leaving them in produced a sidebar that read
# "Evidence, Evidence, Evidence" between chapters.
UNLISTED_DIRS = {"runs", "core", "prod"}


def build_sidebar() -> list:
    """Generate the sidebar explicitly instead of letting Docusaurus infer it.

    Autogeneration walks every directory, so every `runs/`, `core/` and `prod/`
    folder became a nav category. Building it here means the tree contains
    chapters and nothing else.
    """

    def leaf(page: Path, rel: Path):
        """A page that is not a directory: a landscape table, a standard, a lane
        guide. It already carries its own nav label and position, written into
        the generated frontmatter, so read them back rather than guessing.
        """
        label, position = page.stem, DEFAULT_POSITION
        lines = page.read_text().splitlines()
        for line in lines[1:] if lines[:1] == ["---"] else []:
            if line == "---":
                break
            if line.startswith("sidebar_label:"):
                label = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("sidebar_position:"):
                position = int(line.split(":", 1)[1].strip())
        return {
            "type": "doc",
            "id": f"{rel.as_posix()}/{page.stem}",
            "label": label,
            "_position": position,
        }

    def node(directory: Path):
        rel = directory.relative_to(OUT)
        children = []
        for child in sorted(directory.iterdir()):
            if child.is_dir():
                if child.name in UNLISTED_DIRS:
                    continue
                if not (child / "index.md").exists() and not (child / "index.mdx").exists():
                    continue
                children.append(node(child))
            elif child.suffix in {".md", ".mdx"} and child.stem not in {"index", *UNLISTED_DIRS}:
                children.append(leaf(child, rel))
        children.sort(key=lambda entry: (entry["_position"], entry["label"]))
        doc_id = f"{rel.as_posix()}/index"
        label = SIDEBAR_LABELS.get(rel.as_posix(), rel.name)
        position = SIDEBAR_POSITIONS.get(rel.as_posix(), DEFAULT_POSITION)
        if not children:
            return {"type": "doc", "id": doc_id, "label": label, "_position": position}
        return {
            "type": "category",
            "label": label,
            "link": {"type": "doc", "id": doc_id},
            "items": [{k: v for k, v in c.items() if k != "_position"} for c in children],
            "_position": position,
        }

    # The landing page is a doc like any other, and without it here Docusaurus
    # renders `/` with no sidebar at all — a reader who arrives at the front
    # door gets four inline links and no way to see the curriculum.
    top = [
        {"type": "doc", "id": "index", "label": "Start here"},
        {"type": "doc", "id": "topics", "label": "Read by topic", "_position": 10},
    ]
    for section, base_pos in SECTIONS:
        directory = OUT / section
        if not directory.is_dir():
            continue
        entry = node(directory)
        entry["label"] = TITLE_OVERRIDES[section]
        entry["_position"] = base_pos
        top.append(entry)
    top[1:] = sorted(top[1:], key=lambda entry: entry["_position"])
    return [{k: v for k, v in entry.items() if k != "_position"} for entry in top]


SIDEBAR_LABELS: dict[str, str] = {}
SIDEBAR_POSITIONS: dict[str, int] = {}


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

    # Landing page and the topic index are maintained by hand: the landing
    # page carries the interactive demo, and the topic index cuts across
    # every section, which the per-directory sidebar below cannot express.
    here_dir = Path(__file__).resolve().parent
    landing = here_dir / "landing.mdx"
    if landing.exists():
        shutil.copy(landing, OUT / "index.mdx")
    topics = here_dir / "topics.mdx"
    if topics.exists():
        shutil.copy(topics, OUT / "topics.mdx")

    count = 0
    # What every chapter costs to read, keyed by its repository path, which is
    # also its route below /playground/. `ReadingMap.tsx` sums these to declare
    # what a route costs before the reader starts it. Emitted rather than typed
    # for the same reason the per-page badge is: a number nobody writes cannot
    # drift away from the prose it describes.
    page_cost: dict[str, dict[str, object]] = {}
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
        # Kept beside dir_meta rather than widening it: `write_category_files`
        # consumes that shape, and the section listing is the only thing that
        # wants what a chapter costs to read.
        dir_cost: dict[Path, tuple[str, int]] = {}
        for src in sorted(src_dir.rglob("*.md")):
            rel = src.relative_to(ROOT)
            dest_rel = rel.with_name("index.md") if src.name == "README.md" else rel
            title, position, nav_label, level, minutes = convert(src, OUT / dest_rel, None)
            if src.name == "README.md":
                dir_cost[rel.parent] = (level, minutes)
                page_cost[rel.parent.as_posix()] = {"level": level, "minutes": minutes}
                key = dest_rel.parent.as_posix()
                SIDEBAR_LABELS[key] = nav_label
                SIDEBAR_POSITIONS[key] = position
            if src.name == "README.md" and rel.parent != Path(section):
                dir_meta[rel.parent] = (title, position)
            count += 1

        # Section roots are linked to as directories (e.g. ../../platform/) but
        # have no README of their own, so give them a landing page.
        if not (src_dir / "README.md").exists():
            children = [
                (dir_meta.get(Path(section) / d.name, (d.name, DEFAULT_POSITION)), d.name)
                for d in src_dir.iterdir()
                if d.is_dir() and (d / "README.md").exists()
            ]
            # Curriculum order, not alphabetical. The listing used to sort by
            # the displayed title, which only looked right while every title
            # began with its position ("02 — Data"). Sort by the position the
            # manifest assigns, and fall back to the title for ties.
            children.sort(key=lambda entry: (entry[0][1], entry[0][0]))

            listing = "\n".join(
                f"- [{meta[0]}]({name}/){cost_suffix(dir_cost, section, name)}"
                for meta, name in children
            )
            intro = SECTION_INTROS.get(section, "")
            body = f"{intro}\n\n{listing}" if intro else listing
            (OUT / section / "index.md").write_text(
                f'---\ntitle: "{TITLE_OVERRIDES[section]}"\n---\n\n{body}\n'
            )

        write_category_files(section, dir_meta)

        # Images and charts referenced by those pages. This walks the same
        # ASSET_SUFFIXES the link rewriter honours: hardcoding ".png" here
        # meant an SVG chart passed every local check and then failed the
        # Docusaurus build on an unresolvable image.
        for img in sorted(src_dir.rglob("*")):
            if img.suffix.lower() not in ASSET_SUFFIXES:
                continue
            rel = img.relative_to(ROOT)
            (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, OUT / rel)

    sidebar = build_sidebar()
    here = Path(__file__).resolve().parent
    (here / "sidebars.generated.json").write_text(json.dumps(sidebar, indent=2) + "\n")
    (here / "src" / "reading-cost.generated.json").write_text(
        json.dumps(dict(sorted(page_cost.items())), indent=2) + "\n"
    )

    print(f"synced {count} pages from the repository into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
