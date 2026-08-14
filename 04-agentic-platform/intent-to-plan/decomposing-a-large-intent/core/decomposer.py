"""A rule-based intent decomposer over the mission's real task records.

The intent-to-plan stage claims a large intent is a constraint set whose
satisfaction requires several leaves plus ordering decisions. This file makes
that claim mechanical, with no model in the loop:

1. Verifiability — every leaf has a done condition (a target test and a
   test command). A leaf without one cannot be scored, so it is not a leaf.
2. Topology grouping — leaves are grouped by shared source files, not by the
   intent's nouns. Two tasks that touch the same file are not independent
   parallel leaves; they contend on that file (the marcus #267 finding).
3. Coupling warnings — pairs whose file overlap exceeds a threshold are one
   serial lane, not parallel work. The threshold is marcus's 30%.
4. QA separation — the decomposer proves the shape; it does not assign order
   inside a lane and does not claim the split is correct. Ordering within a
   lane is the designer's decision, made against the design doc.

The contrast the chapter cares about is between an intent and a tree: the
same sentences can be read as a flat list, a wide fan-out, or a width-2 DAG,
and only the code topology decides which is safe to execute.

Run:
    python decomposer.py --tasks ../../../tasks/candidates.jsonl \
        --intent "Make the repository's correctness signals green again"
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

OVERLAP_THRESHOLD = 0.3  # marcus #267: overlap > 30% -> switch strategy


@dataclass(frozen=True)
class Leaf:
    task_id: str
    subject: str
    source_files: tuple[str, ...]
    target_tests: tuple[str, ...]
    test_command: tuple[str, ...]

    @property
    def verifiable(self) -> bool:
        """A leaf is a constraint set with a machine-checkable done condition."""
        return bool(self.target_tests) and bool(self.test_command)


def load_leaves(path: Path) -> list[Leaf]:
    leaves: list[Leaf] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        leaves.append(
            Leaf(
                task_id=record["task_id"],
                subject=record.get("subject", ""),
                source_files=tuple(record.get("source_files", [])),
                target_tests=tuple(record.get("target_tests", [])),
                test_command=tuple(record.get("test_command", [])),
            )
        )
    return leaves


def containment_overlap(a: Leaf, b: Leaf) -> float:
    """How much of the smaller task's file set the other task also touches.

    Shared-file count is the operational collision risk: whoever runs second
    on a shared file may conflict with the first writer. Normalizing by the
    smaller file set measures how much of a task's work is exposed to that
    collision, which is what the marcus threshold is about.
    """
    a_files = set(a.source_files)
    b_files = set(b.source_files)
    shared = a_files & b_files
    if not shared:
        return 0.0
    return len(shared) / min(len(a_files), len(b_files))


def lane_components(leaves: list[Leaf]) -> list[list[Leaf]]:
    """Connected components of the shared-file graph.

    Two leaves that share a source file are in the same lane: they cannot run
    as fully independent agents without contending on that file. Components
    are the tree's subtrees, derived from code topology instead of intent
    nouns.
    """
    index = {leaf.task_id: leaf for leaf in leaves}
    parent = {task_id: task_id for task_id in index}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for a, b in combinations(leaves, 2):
        if set(a.source_files) & set(b.source_files):
            union(a.task_id, b.task_id)

    by_root: dict[str, list[Leaf]] = {}
    for leaf in leaves:
        by_root.setdefault(find(leaf.task_id), []).append(leaf)
    return list(by_root.values())


def coupling_pairs(leaves: list[Leaf], threshold: float) -> list[tuple[Leaf, Leaf, float]]:
    """Pairs whose file overlap exceeds the threshold: not parallel work."""
    flagged: list[tuple[Leaf, Leaf, float]] = []
    for a, b in combinations(leaves, 2):
        overlap = containment_overlap(a, b)
        if overlap >= threshold:
            flagged.append((a, b, overlap))
    return flagged


def lane_is_clique(lane: list[Leaf]) -> bool:
    """Every pair in the lane shares a file: the lane is serial, not fan-out."""
    for a, b in combinations(lane, 2):
        if not (set(a.source_files) & set(b.source_files)):
            return False
    return True


def shared_files(lane: list[Leaf]) -> tuple[str, ...]:
    files = {f for leaf in lane for f in leaf.source_files}
    per_leaf = [set(leaf.source_files) for leaf in lane]
    common = files
    for leaf_files in per_leaf:
        common &= leaf_files
    return tuple(sorted(common))


def render_tree(
    intent: str,
    leaves: list[Leaf],
    lanes: list[list[Leaf]],
    flagged: list[tuple[Leaf, Leaf, float]],
) -> str:
    lines = [f"INTENT: {intent}", ""]
    lane_lines: list[str] = []
    for i, lane in enumerate(lanes, start=1):
        shared = shared_files(lane)
        if len(lane) == 1:
            kind = "independent"
            touch = f"touches {', '.join(shared) or '(no files)'}"
        elif lane_is_clique(lane):
            kind = "coupled -> serial"
            touch = f"shares {', '.join(shared) or '(no shared file)'}"
        else:
            kind = "shared files -> inspect"
            touch = f"shares {', '.join(shared) or '(no shared file)'}"
        leaf_word = "leaf" if len(lane) == 1 else "leaves"
        label = (
            f"Lane {i} · {touch} ({len(lane)} {leaf_word}) · {kind}"
        )
        lane_lines.append(label)
        for j, leaf in enumerate(lane):
            marker = "└──" if j == len(lane) - 1 else "├──"
            done = " ".join(leaf.target_tests) or "(no test)"
            lane_lines.append(f"{marker} {leaf.task_id}  {leaf.subject}  [done: {done}]")
        if i < len(lanes):
            lane_lines.append("")
    lines.extend(lane_lines)
    lines.append("")

    verifiable = [leaf for leaf in leaves if leaf.verifiable]
    lane_word = "lane" if len(lanes) == 1 else "lanes"
    lines.append(f"Invariant 1 — leaves independently verifiable: {len(verifiable)}/{len(leaves)}")
    lines.append(f"Invariant 2 — explicit dependencies: {len(lanes)} {lane_word}, "
                 f"{len(flagged)} coupled pair(s) flagged")
    lines.append("Invariant 3 — collective sufficiency: not mechanically checkable "
                 "without a constraint list for the intent; reviewer's call")
    lines.append("Invariant 4 — QA separated from completion: no order assigned "
                 "inside a lane; no correctness claim")
    lines.append(f"DAG width (parallel lanes): {len(lanes)}")
    if flagged:
        lines.append("")
        lines.append("Coupled pairs (overlap >= 0.30):")
        for a, b, overlap in flagged:
            lines.append(
                f"  {a.task_id} <-> {b.task_id}  overlap {overlap:.2f}  "
                f"shared {sorted(set(a.source_files) & set(b.source_files))}"
            )
        lines.append("Recommendation: do not fan these out; merge into one lane or "
                     "split by layer after the design doc exists (marcus #267).")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", required=True, help="path to a tasks/*.jsonl")
    ap.add_argument("--intent", default="(default intent)", help="the large intent text")
    ap.add_argument("--json", action="store_true", help="emit machine-readable verdicts")
    args = ap.parse_args()

    leaves = load_leaves(Path(args.tasks))
    lanes = lane_components(leaves)
    flagged = coupling_pairs(leaves, OVERLAP_THRESHOLD)

    if args.json:
        report = {
            "source": Path(args.tasks).name,
            "intent": args.intent,
            "leaves": [
                {
                    "task_id": leaf.task_id,
                    "subject": leaf.subject,
                    "source_files": list(leaf.source_files),
                    "target_tests": list(leaf.target_tests),
                    "verifiable": leaf.verifiable,
                }
                for leaf in leaves
            ],
            "lanes": [
                {
                    "lane": i,
                    "shared_files": list(shared_files(lane)),
                    "clique": lane_is_clique(lane),
                    "task_ids": [leaf.task_id for leaf in lane],
                }
                for i, lane in enumerate(lanes, start=1)
            ],
            "coupling_pairs": [
                {"a": a.task_id, "b": b.task_id, "overlap": round(overlap, 2)}
                for a, b, overlap in flagged
            ],
            "dag_width": len(lanes),
            "verdicts": {
                "leaf_verifiable": len([leaf for leaf in leaves if leaf.verifiable]),
                "leaves_total": len(leaves),
                "sufficiency": "not mechanically checkable",
                "qa_separation": True,
            },
        }
        print(json.dumps(report, indent=2))
        return

    print(render_tree(args.intent, leaves, lanes, flagged))
    print()
    lane_word = "lane" if len(lanes) == 1 else "lanes"
    print(
        f"{len(leaves)} leaves, {len(lanes)} {lane_word}, {len(flagged)} coupled pairs; "
        "no model called. Order inside a lane is left to the design review."
    )


if __name__ == "__main__":
    main()
