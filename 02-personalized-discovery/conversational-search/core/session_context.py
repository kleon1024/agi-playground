"""Conversational search, read: the follow-up that needs the first turn.

Stage 36 is the frontier of search: a multi-turn session where the
second query is only meaningful with the first. This script reads how
session context resolves an ambiguous follow-up.

Run:
    uv run python core/session_context.py
    uv run python core/session_context.py --emit-log /tmp/session-envelope.json

The `--emit-log` flag writes the audit cohort: 10 sessions — 5 short
(whole context fits the window) and 5 long (the context is truncated) —
with the resolution score of a follow-up that refers back to the first
turn. The production path in `prod/conversation_audit.py` stratifies
resolution by session length, the case-finding that shows when the
session stops resolving.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: resolution of a follow-up that needs the first turn,
# per session. Short sessions keep the whole context, so the first-turn
# grounding resolves; long sessions truncate oldest-first, and the
# first-turn topic is the first thing to fall out of the window.
AUDIT_SESSIONS = {
    "head": [
        {"turns": 2, "followup": "and the cheaper ones", "resolution": 1.0},
        {"turns": 3, "followup": "what about trail versions", "resolution": 1.0},
        {"turns": 3, "followup": "which fit wide feet", "resolution": 1.0},
        {"turns": 4, "followup": "same in waterproof", "resolution": 0.9},
        {"turns": 4, "followup": "and the orange colorway", "resolution": 1.0},
    ],
    "tail": [
        {"turns": 12, "followup": "back to the first pair", "resolution": 0.6},
        {"turns": 15, "followup": "and the ones from turn one", "resolution": 0.4},
        {"turns": 18, "followup": "compare with the original", "resolution": 0.4},
        {"turns": 20, "followup": "go back to what we started with", "resolution": 0.3},
        {"turns": 24, "followup": "and the cheap ones from the start", "resolution": 0.2},
    ],
}


def render() -> None:
    first = "best running shoes for marathons"
    follow_up = "what about the cheaper ones"
    # Candidate intents for the follow-up, scored with and without context.
    candidates = [
        ("cheaper marathon shoes", 0.8, 0.2),
        ("cheaper headphones", 0.1, 0.6),
        ("cheaper laptops", 0.1, 0.2),
    ]
    print("conversational search, read:")
    print(f"  turn 1: '{first}'")
    print(f"  turn 2: '{follow_up}'")
    print("  candidate intents (with context, without):")
    for name, with_ctx, without in candidates:
        print(f"    {name}: {with_ctx} vs {without}")
    winner = max(candidates, key=lambda x: x[1])
    print(f"  resolved: {winner[0]}")
    print("\nreading: without context the follow-up is ambiguous; with the")
    print("session it resolves to the cheaper marathon shoes. The query")
    print("is only part of the input — the session is the other part.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"sessions": AUDIT_SESSIONS}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
