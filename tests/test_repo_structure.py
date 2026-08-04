import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SOURCE_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mdx",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_DIRECTORY_NAMES = {
    ".docusaurus",
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "node_modules",
    # A fetched, gitignored dataset or source-repo cache (e.g. mission 04's
    # cloned public repo) is not authored content.
    "cache",
}
IGNORED_SOURCE_PATHS = {
    "site/docs",
}

# The five layers. "Business goal" and "outcome telemetry" are not directories —
# they live inside each mission's contract, which is why the mission test below
# checks for a contract rather than for more folders.
FOUNDATIONS = ["01-first-training-loop"]

PLATFORM = [
    "data",
    "evaluation-observability",
    "safety-governance",
]

MISSIONS = [
    "01-language-model-agent",
    "02-personalized-discovery",
    "03-quantitative-research",
    "04-code-agent",
]

# reference/standards/mission-contract.md names these and calls the last two the fields
# that keep the repo honest. Checking they are present is the difference
# between a contract and a suggestion.
MISSION_CONTRACT_FIELDS = [
    "stakeholder",
    "job",
    "decision",
    "baseline",
    "primary_metric",
    "guardrails",
    "latency_budget",
    "cost_budget",
    "capabilities",
    "acceptance",
    "proves",
    "does_not_prove",
]

MISSION_01_STAGES = [
    "00-corpus",
    "01-tokenizer",
    "02-pretrain",
    "03-sft",
    "04-rl",
    "05-serve",
    "06-agent",
    "07-eval",
]


def test_foundations_lessons_exist():
    for name in FOUNDATIONS:
        assert (ROOT / "foundations" / name / "README.md").is_file()


def test_platform_layers_exist():
    for name in PLATFORM:
        assert (ROOT / "platform" / name / "README.md").is_file(), f"missing platform/{name}"


def test_a_shared_chapter_stays_in_the_mission_that_built_it():
    """There is no `capabilities/` directory, and reuse does not create one.

    It existed for one chapter -- the agent harness -- and held a second, fuller
    telling of mission 01 stage 06 with no `core/`, `prod/`, or `runs/` beside
    it. Separating an explanation from the run that backs it is how a chapter
    ends up making a claim with no evidence attached, which is the one thing
    this repository is built not to do. A second consumer now links to the
    chapter where it was measured.
    """
    assert not (ROOT / "capabilities").exists(), (
        "reuse means a second mission links to the chapter where it was "
        "measured, not that the chapter moves into a directory of its own"
    )
    harness = ROOT / "missions" / "01-language-model-agent" / "06-agent"
    for consumer in (
        ROOT / "missions" / "02-personalized-discovery" / "07-rule-engine" / "README.md",
        ROOT / "missions" / "04-code-agent" / "README.md",
    ):
        assert "01-language-model-agent/06-agent" in consumer.read_text(), (
            f"{consumer.relative_to(ROOT)} reuses the agent harness but does "
            "not link to it"
        )
    assert (harness / "runs").is_dir(), "the shared chapter kept its evidence"


def test_missions_declare_a_contract():
    """A mission without a contract is a demo, not a mission."""
    for name in MISSIONS:
        mission = ROOT / "missions" / name
        assert (mission / "README.md").is_file(), f"missing missions/{name}/README.md"
        contract = mission / "mission.yaml"
        assert contract.is_file(), (
            f"missions/{name} has no mission.yaml — every mission must declare "
            "stakeholder, job, decision, baseline, primary_metric, guardrails, "
            "budgets, capabilities, and acceptance before it is built"
        )
        # Parsed by regex on top-level keys rather than with PyYAML, because
        # the default test environment carries no dependencies beyond pytest
        # and ruff, and a structural check should not be the thing that
        # changes that.
        keys = set(re.findall(r"^([a-z_]+):", contract.read_text(), re.MULTILINE))
        missing = [f for f in MISSION_CONTRACT_FIELDS if f not in keys]
        assert not missing, (
            f"missions/{name}/mission.yaml is missing {missing}. "
            "reference/standards/mission-contract.md requires every field; proves and "
            "does_not_prove are what stop a mission from claiming an outcome "
            "it only proxied."
        )


def test_mission_01_stages_exist():
    for name in MISSION_01_STAGES:
        readme = ROOT / "missions" / "01-language-model-agent" / name / "README.md"
        assert readme.is_file(), f"missing {readme}"


# Trees where a lesson trains, adapts, serves, or evaluates a model, and must
# therefore say which weights its claims rest on. Mission 02 and 03 stages are
# recommender and quantitative work with no language-model base, so the
# declaration would be noise there rather than a check.
BASE_DECLARING_TREES = ["foundations", "platform", "missions/01-language-model-agent"]
BASE_PATTERN = re.compile(r"^base: (scratch|none|external:\S+)$", re.MULTILINE)


def _lesson_readmes(tree: str):
    """A lesson is a directory holding both a README and a `core/`."""
    for readme in sorted((ROOT / tree).rglob("README.md")):
        if (readme.parent / "core").is_dir():
            yield readme


def test_every_lesson_declares_its_base_model():
    """Track A (from-scratch) and Track B (published checkpoint) are not
    interchangeable, and the difference is invisible in a loss curve. See the
    GRPO zero-advantage argument in reference/standards/lesson-and-run-contract.md.
    """
    missing = []
    for tree in BASE_DECLARING_TREES:
        for readme in _lesson_readmes(tree):
            head = readme.read_text().split("\n---\n", 1)[0]
            if not BASE_PATTERN.search(head):
                missing.append(readme.relative_to(ROOT).as_posix())
    assert not missing, (
        "every lesson must declare `base: scratch`, `base: none`, or "
        "`base: external:<model-id>` in its frontmatter:\n" + "\n".join(missing)
    )


def test_every_published_page_declares_its_level():
    """Difficulty is not curriculum position, and the sidebar only carries one.

    Before this field the repository published 80 pages and 80,436 words with
    nothing anywhere saying which of them were prerequisites and which were
    frontier claims. A reader's only ordering signal was the sidebar, which
    encodes where a chapter sits in the curriculum, not what it assumes of you.
    `reference` is a real answer -- standards, runbooks and research passes are
    lookup surfaces, not rungs on the ladder.
    """
    allowed = {"foundation", "applied", "frontier", "reference"}
    pattern = re.compile(r"^level:\s*(\S+)\s*$", re.MULTILINE)
    problems = []
    for section in ("foundations", "missions", "platform",
                    "infra", "reference"):
        for page in sorted((ROOT / section).rglob("*.md")):
            if {"core", "prod", "runs", "cache"} & set(page.parts):
                continue
            rel = page.relative_to(ROOT).as_posix()
            head = page.read_text().split("\n---\n", 1)[0]
            found = pattern.search(head)
            if not found:
                problems.append(f"{rel}: no `level:` in frontmatter")
            elif found.group(1) not in allowed:
                problems.append(f"{rel}: level `{found.group(1)}` is not one of {sorted(allowed)}")
    assert not problems, "\n".join(problems)


def test_currency_amounts_are_escaped_in_prose():
    """A bare `$` opens KaTeX math, and the next one closes it.

    Two dollar amounts in the same chapter -- "$0.16 per resolved task on the
    cheapest tier against $0.82 on the most expensive" -- render as one
    unbreakable math run reading `0.16perresolvedtaskonthecheapestieragainst`,
    which also overflows the page on a phone. Six published pages shipped this
    way, because the site builds cleanly and the damage is only visible in a
    browser. Escape money as `\\$`; real math is unaffected because a formula
    that means to be a formula opens and closes deliberately.
    """
    problems = []
    for section in ("foundations", "missions", "platform",
                    "infra", "reference"):
        for page in sorted((ROOT / section).rglob("*.md")):
            if {"core", "prod", "cache"} & set(page.parts):
                continue
            text = page.read_text()
            rel = page.relative_to(ROOT).as_posix()
            for offset in _bare_currency_offsets(text):
                line = text.count("\n", 0, offset) + 1
                problems.append(f"{rel}:{line}: unescaped currency `$` -- write `\\$`")
    assert not problems, "\n".join(problems)


_FENCE = re.compile(r"^\s*```")
_INLINE_CODE = re.compile(r"`[^`]*`")
_UNESCAPED_DOLLAR = re.compile(r"(?<!\\)\$")
_PROSE_WORD = re.compile(r"[A-Za-z]{2}")


def _mask_code(text):
    """Blank out fenced blocks and inline code, preserving every offset."""
    masked, in_fence = [], False
    for line in text.split("\n"):
        if _FENCE.match(line):
            in_fence = not in_fence
            masked.append(" " * len(line))
        elif in_fence:
            masked.append(" " * len(line))
        else:
            masked.append(_INLINE_CODE.sub(lambda m: " " * len(m.group()), line))
    return "\n".join(masked)


def _bare_currency_offsets(text):
    """Offsets of `$` characters that open an amount rather than a formula.

    Two things separate them. A formula is symbols: it carries a LaTeX escape,
    a subscript or a superscript, or it holds no prose word at all. The text
    between two prices is a sentence. Pairing runs over the whole document
    rather than line by line, because both a display formula and the sentence
    this test exists to protect can span several lines.
    """
    masked = _mask_code(text)
    marks = [m.start() for m in _UNESCAPED_DOLLAR.finditer(masked)]
    found, index = [], 0
    while index < len(marks):
        start = marks[index]
        if index + 1 < len(marks) and marks[index + 1] == start + 1:
            close = next((j for j in range(index + 2, len(marks) - 1)
                          if marks[j + 1] == marks[j] + 1), None)
            index = close + 2 if close is not None else index + 2
            continue
        after = masked[start + 1:start + 3].lstrip()[:1]
        money_shaped = after.isdigit() or after == "/"
        if index + 1 < len(marks):
            span = masked[start + 1:marks[index + 1]]
            if any(ch in span for ch in "\\^_{") or not _PROSE_WORD.search(span):
                index += 2
                continue
            if money_shaped:
                found.append(start)
            index += 1
            continue
        if money_shaped:
            found.append(start)
        index += 1
    return found


def test_top_level_docs_exist():
    for rel in [
        "README.md",
        "LICENSE",
        "AGENTS.md",
        "reference/README.md",
        "reference/research/README.md",
        "infra/README.md",
        "reference/standards/README.md",
        "reference/standards/mission-contract.md",
        "reference/standards/lesson-and-run-contract.md",
    ]:
        assert (ROOT / rel).is_file(), f"missing {rel}"


def _is_emoji(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x1F000 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
        or codepoint
        in {
            0x20E3,
            0x23E9,
            0x23EA,
            0x23EB,
            0x23EC,
            0x23F0,
            0x23F3,
            0x23F8,
            0x23F9,
            0x23FA,
            0x25B6,
            0x25C0,
            0xFE0F,
        }
    )


def test_authored_sources_do_not_contain_emoji():
    failures = []
    for directory, child_directories, filenames in os.walk(ROOT):
        parent = Path(directory)
        child_directories[:] = [
            child
            for child in child_directories
            if child not in IGNORED_DIRECTORY_NAMES
            and not any(
                (parent / child).relative_to(ROOT).as_posix() == ignored
                or (parent / child).relative_to(ROOT).as_posix().startswith(f"{ignored}/")
                for ignored in IGNORED_SOURCE_PATHS
            )
        ]
        for filename in filenames:
            path = parent / filename
            if path.suffix.lower() not in TEXT_SOURCE_SUFFIXES:
                continue
            relative = path.relative_to(ROOT)
            for line_number, line in enumerate(path.read_text().splitlines(), start=1):
                found = "".join(sorted({char for char in line if _is_emoji(char)}))
                if found:
                    failures.append(f"{relative}:{line_number}: {found}")
    assert not failures, "emoji are not allowed in authored sources:\n" + "\n".join(failures)


def test_claude_instructions_share_the_agent_source():
    claude_instructions = ROOT / "CLAUDE.md"
    assert claude_instructions.is_symlink()
    assert claude_instructions.readlink() == Path("AGENTS.md")
