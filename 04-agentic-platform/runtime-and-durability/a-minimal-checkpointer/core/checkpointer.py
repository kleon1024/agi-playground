"""Checkpoint-and-resume for a multi-step task, demonstrated on real tasks.

The runtime-and-durability stage claims a long task must survive a crash:
every step's state is written somewhere resumable, and a killed process
restarts from the checkpoint instead of from zero. This file demonstrates
the mechanics on the mission's real task list: each task is a step with
idempotent work, a checkpoint file records completion, and a simulated
crash at a chosen step proves the resume path.

The work per step is deliberately trivial (hash the task id against a seed)
so the demo isolates the durability mechanics from the work itself. The
claim is about resumability, not about the task.

Run:
    python checkpointer.py --tasks ../../../tasks/private.jsonl \
        --checkpoint /tmp/ckpt.json --crash-at 1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path


def step_work(task_id: str, seed: int) -> str:
    """Deterministic, idempotent per-step work."""
    return hashlib.sha256(f"{task_id}:{seed}".encode()).hexdigest()[:12]


def load_checkpoint(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"done": [], "attempts": 0}


def save_checkpoint(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--checkpoint", default="/tmp/ckpt.json")
    ap.add_argument("--crash-at", type=int, default=-1,
                    help="simulate a crash before this step index")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    ckpt = Path(args.checkpoint)
    tasks = [json.loads(l) for l in Path(args.tasks).read_text().splitlines() if l.strip()]
    task_ids = [t["task_id"] for t in tasks]

    state = load_checkpoint(ckpt)
    completed = set(state["done"])

    started = time.monotonic()
    for idx, task_id in enumerate(task_ids):
        if task_id in completed:
            print(f"[resumed] {task_id} already done")
            continue
        if args.crash_at >= 0 and idx == args.crash_at:
            print(f"[crash]   simulated crash before step {idx} ({task_id})")
            state["attempts"] += 1
            save_checkpoint(ckpt, state)
            raise SystemExit(3)
        result = step_work(task_id, args.seed)
        completed.add(task_id)
        state["done"] = sorted(completed)
        state["attempts"] += 1
        save_checkpoint(ckpt, state)
        print(f"[done]    {task_id} -> {result}")

    print(
        f"\nall {len(task_ids)} steps complete in "
        f"{round(time.monotonic() - started, 3)}s; "
        f"attempts={state['attempts']} (resumed steps are not redone)."
    )


if __name__ == "__main__":
    main()
