import os
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
    "training",
    "adaptation/post-training",
    "adaptation/reinforcement-learning",
    "serving",
    "evaluation-observability",
    "safety-governance",
]

CAPABILITIES = ["act-coordinate"]

MISSIONS = ["01-language-model-agent", "02-personalized-discovery"]

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


def test_capabilities_exist():
    for name in CAPABILITIES:
        assert (ROOT / "capabilities" / name / "README.md").is_file()


def test_missions_declare_a_contract():
    """A mission without a contract is a demo, not a mission."""
    for name in MISSIONS:
        mission = ROOT / "missions" / name
        assert (mission / "README.md").is_file(), f"missing missions/{name}/README.md"
        assert (mission / "mission.yaml").is_file(), (
            f"missions/{name} has no mission.yaml — every mission must declare "
            "stakeholder, job, decision, baseline, primary_metric, guardrails, "
            "budgets, capabilities, and acceptance before it is built"
        )


def test_mission_01_stages_exist():
    for name in MISSION_01_STAGES:
        readme = ROOT / "missions" / "01-language-model-agent" / name / "README.md"
        assert readme.is_file(), f"missing {readme}"


def test_top_level_docs_exist():
    for rel in [
        "README.md",
        "LICENSE",
        "AGENTS.md",
        "research/README.md",
        "infra/README.md",
        "standards/README.md",
        "standards/mission-contract.md",
        "standards/lesson-and-run-contract.md",
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
