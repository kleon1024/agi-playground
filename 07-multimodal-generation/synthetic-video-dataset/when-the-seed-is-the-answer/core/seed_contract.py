"""The seed contract, read: what makes a clip scoreable without real footage.

Stage 00's committed fixture manifest holds six clips whose seed fully
determines the correct frames: a prompt ("a yellow square moving
down_right") plus a motion dict, rendered deterministically. This script
reads the manifest and lays out the contract — the fields that make a
completion checkable against a real answer rather than judged by eye.

Input (recorded, unchanged): ../fixtures/manifest.jsonl

Run:
    uv run python core/seed_contract.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    lines = [
        json.loads(ln)
        for ln in (
            Path(__file__).resolve().parents[2] / "fixtures" / "manifest.jsonl"
        ).read_text().splitlines()
        if ln.strip()
    ]
    print(f"fixture manifest: {len(lines)} clips, seed -> prompt -> frames")
    for clip in lines[:3]:
        m = clip["motion"]
        print(
            f"  {clip['id']} seed {clip['seed']}: {clip['prompt']} | "
            f"{m['shape']} {m['color']}, {m['direction']} speed {m['speed']} "
            f"x0 {m['x0']} y0 {m['y0']} | {len(clip['frames'])} frames"
        )
    print("\nreading: the seed is the answer key — the same seed always")
    print("renders the same frames, which is what lets a generated completion")
    print("be checked mechanically instead of judged by eye.")


if __name__ == "__main__":
    main()
