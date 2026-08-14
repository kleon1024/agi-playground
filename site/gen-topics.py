"""Generate the "Read by topic" index from the content graph.

The index used to be a hand-written list of decision-question headings that
drifted away from the tree it described. It is generated now, from the same
graph that orders the sidebar and resolves links, so a new chapter appears here
the moment it enters the graph and every link is correct by construction.
`tests/test_sync_docs.py` still enforces that every published chapter appears
at least once, as a backstop rather than as the only guard.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_FILE = ROOT / "reference" / "standards" / "content-graph.json"
OUT = ROOT / "site" / "topics.mdx"

SECTIONS = [
    ("01-language-model", "Raw text to a tool-using model"),
    ("02-personalized-discovery", "Personalized discovery"),
    ("03-quantitative-research", "Quantitative research"),
    ("04-agentic-platform", "Agentic platform"),
    ("05-game-ai", "Game AI"),
    ("07-multimodal-generation", "Multimodal generation"),
    ("08-bio-pharma-modeling", "Bio-pharma modeling"),
    ("09-autonomous-driving", "Autonomous driving"),
    ("foundations", "Foundations"),
    ("reference", "Reference"),
]

# Topic 01's stages read as three phases; the headings make the
# pretraining / post-training boundary explicit without a directory for it.
PHASES = {
    "pretraining": ["corpus", "tokenizer", "pretrain"],
    "post-training": ["sft", "rl"],
    "runtime": ["serve", "agent-harness", "eval"],
}

# Cross-cutting reading lists. Chapters may appear here and under their own
# topic: the coverage test allows a chapter to answer two questions.
RISK_GOVERNANCE = [
    "01-language-model/eval/red-teaming",
    "01-language-model/eval/eval-gates",
    "01-language-model/eval/who-decides-to-ship",
    "02-personalized-discovery/fairness-and-allocation",
    "02-personalized-discovery/privacy-safe-attribution",
    "04-agentic-platform/verification-and-evals/control-plane-governance",
    "04-agentic-platform/verification-and-evals/the-adversary-that-adapts",
]


def title_of(path: str) -> str:
    entry = GRAPH_BY_PATH.get(path)
    if entry and entry.get("title"):
        return entry["title"]
    name = path.split("/")[-1]
    return name.replace("-", " ").replace("_", " ").strip().title() or "Overview"


def route(path: str) -> str:
    return f"/playground/{path}"


def bullet(path: str) -> str:
    return f"- [{title_of(path)}]({route(path)})"


def emit_stage_tree(stage: str, lines: list[str]) -> None:
    """The stage, then its sub-chapters and owned pages, in graph order."""
    lines.append(bullet(stage))
    children = sorted(
        (c for c in GRAPH_BY_PATH.values() if c["path"].startswith(stage + "/")),
        key=lambda c: (c["order"], c["path"]),
    )
    for child in children:
        lines.append(bullet(child["path"]))


def main() -> None:
    global GRAPH_BY_PATH
    graph = json.loads(GRAPH_FILE.read_text())
    GRAPH_BY_PATH = {c["path"]: c for c in graph["chapters"]}
    groups = graph.get("groups", {})

    lines = [
        "---",
        "title: Read by topic",
        "description: Every chapter in this repository, grouped by the system it serves.",
        "---",
        "",
        "# Which system are you trying to build?",
        "",
        "The sidebar groups chapters by who owns them. This page groups them by the",
        "system you are building, in the order the argument builds: the topic that",
        "owns the outcome, its stages, and the sub-chapters that deepen each stage.",
        "Every published chapter appears here at least once; this page is generated",
        "from the same content graph that orders the sidebar, so it cannot drift.",
        "",
    ]

    for section, _ in SECTIONS:
        section_entries = sorted(
            (c for c in GRAPH_BY_PATH.values() if c["path"].startswith(section + "/")),
            key=lambda c: (c["order"], c["path"]),
        )
        heading = title_of(section)
        lines.append(f"## {heading}")
        lines.append("")

        section_groups = groups.get(section)
        if section_groups:
            grouped_stages = {s for g in section_groups for s in g["stages"]}
            for group in section_groups:
                lines.append(f"### {group['label']}")
                lines.append("")
                for stage in group["stages"]:
                    emit_stage_tree(stage, lines)
                lines.append("")
            leftover = [
                c["path"]
                for c in section_entries
                if c["kind"] in ("sub", "page") and c["path"] not in grouped_stages
                and not any(c["path"].startswith(s + "/") for s in grouped_stages)
            ]
            for path in leftover:
                lines.append(bullet(path))
            if leftover:
                lines.append("")
            continue

        if section == "01-language-model":
            phase_stages = {
                phase: [f"01-language-model/{name}" for name in names]
                for phase, names in PHASES.items()
            }
            all_phase_stages = [
                stage for stages in phase_stages.values() for stage in stages
            ]
            for phase, stages in phase_stages.items():
                lines.append(f"### {phase.replace('-', ' ').title()}")
                lines.append("")
                for stage in stages:
                    emit_stage_tree(stage, lines)
                lines.append("")
            leftover = [
                c["path"]
                for c in section_entries
                if c["path"] not in all_phase_stages
                and not any(c["path"].startswith(s + "/") for s in all_phase_stages)
            ]
            for path in leftover:
                lines.append(bullet(path))
            if leftover:
                lines.append("")
            continue

        for c in section_entries:
            if c["kind"] == "stage":
                emit_stage_tree(c["path"], lines)
            elif c["kind"] == "page" and not any(
                c["path"].startswith(s + "/")
                for s in (e["path"] for e in section_entries if e["kind"] == "stage")
            ):
                lines.append(bullet(c["path"]))
        lines.append("")

    lines += [
        "## When the system is attacked or regulated",
        "",
        "The same guardrails appear in every surface: red-teaming the model, gating",
        "a release, deciding what ships, allocating exposure fairly, protecting",
        "attribution, and governing an agent that acts.",
        "",
    ]
    for path in RISK_GOVERNANCE:
        lines.append(bullet(path))
    lines.append("")
    lines += [
        "## Or start from the stakeholder problem",
        "",
        "Each topic opens with someone who has a decision to make and ends at a",
        "measured outcome with its evidence boundary stated.",
        "",
    ]
    for section, _ in SECTIONS:
        lines.append(bullet(section))
    lines.append("")

    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} with {len(lines)} lines")


if __name__ == "__main__":
    main()
