from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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

MISSIONS = ["01-language-model-agent"]

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
