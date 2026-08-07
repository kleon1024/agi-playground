"""Build the fixed prompt set every author arm answers.

`generate_traces.py` next door holds 3,000 prompts fixed and varies who wrote
the answer. This file does the same thing at a scale a human can read, and adds
one property that run needed and did not have: the prompts are stratified
across every task category the source dataset labels, four per category, so a
per-category breakdown is possible instead of only a pooled average.

Rows come from the *test* split, so they are held out from the 3,000-prompt
training corpus the distillation run built from `train`. Only single-turn rows
are kept, for the reason `generate_traces.py` documents: regenerating the last
assistant turn of a multi-turn conversation leaves the earlier ones human, so
the row belongs to neither arm.

The human reference answer travels with each prompt. It is the fifth arm, and
it is the only arm that cannot be re-generated -- the annotator wrote it once.
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

DEFAULT_DATASET = "HuggingFaceH4/no_robots"


def single_turn_rows(dataset: str, split: str):
    from datasets import load_dataset

    def is_single_turn(turns) -> bool:
        """[user, assistant], optionally behind a leading system turn."""
        if len(turns) == 2:
            return turns[0]["role"] == "user"
        if len(turns) == 3:
            return turns[0]["role"] == "system" and turns[1]["role"] == "user"
        return False

    return [row for row in load_dataset(dataset, split=split) if is_single_turn(row["messages"])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=DEFAULT_DATASET)
    ap.add_argument("--split", default="test")
    ap.add_argument("--per-category", type=int, default=4)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rows = single_turn_rows(args.dataset, args.split)
    by_category = collections.defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)

    out = []
    for category in sorted(by_category):
        for row in by_category[category][: args.per_category]:
            out.append(
                {
                    "id": row["prompt_id"][:12],
                    "category": category,
                    "prompt": row["messages"][-2]["content"],
                    "human": row["messages"][-1]["content"],
                }
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out))
    counts = collections.Counter(r["category"] for r in out)
    print(f"{len(rows)} single-turn rows in {args.split}; wrote {len(out)} prompts")
    for category, n in sorted(counts.items()):
        print(f"  {category:12} {n}")


if __name__ == "__main__":
    main()
