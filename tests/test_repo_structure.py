from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRACKS = [
    "01-foundations", "02-data", "03-pretraining", "04-post-training",
    "05-rl", "06-inference", "07-evals", "08-agents",
]
SPEEDRUN_STAGES = [
    "00-corpus", "01-tokenizer", "02-pretrain", "03-sft",
    "04-rl", "05-serve", "06-agent", "07-eval",
]


def test_tracks_exist_with_readme():
    for name in TRACKS:
        readme = ROOT / "tracks" / name / "README.md"
        assert readme.is_file(), f"missing {readme}"


def test_speedrun_stages_exist_with_readme():
    for name in SPEEDRUN_STAGES:
        readme = ROOT / "speedrun" / name / "README.md"
        assert readme.is_file(), f"missing {readme}"


def test_top_level_docs_exist():
    for rel in ["README.md", "LICENSE", "research/README.md", "infra/README.md"]:
        assert (ROOT / rel).is_file(), f"missing {rel}"
