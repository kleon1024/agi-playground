"""Deterministic demonstration that ContextManager's compaction policy
actually fires as this chapter claims -- no invented mechanism, this runs
core/harness.py's real ContextManager and drop_oldest_tool_results against a
scripted transcript. No model, no network: token counts are chosen so the
budget is crossed at a known point.

Run: python demo_compaction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from harness import ContextManager


def describe(ctx: ContextManager) -> None:
    print(f"  messages={len(ctx.messages)}  tokens={ctx.total_tokens()}  compactions={ctx.compactions}")
    for i, m in enumerate(ctx.messages):
        path = m["meta"].get("read_file_path")
        marker = f"  [read_file_path={path!r}]" if path else ""
        preview = m["content"][:48].replace("\n", " ")
        tok = ctx.token_counter(m["content"])
        print(f"    [{i}] {m['role']:9s} {tok:5d}tok  {preview!r}{marker}")


def demo_a_collapse_before_drop() -> None:
    print("=== Demo A: collapse a superseded read before dropping any turn ===")
    ctx = ContextManager(system_prompt="s" * 40, token_budget=3000)  # system ~10 tok
    action = "a" * 240  # ~60 tok
    small_obs = "o" * 80  # ~20 tok
    big_read = "f" * 7200  # ~1800 tok -- one real read of a real-size file

    ctx.add("assistant", action)
    ctx.add("user", big_read, read_file_path="notes.md")  # first read of notes.md
    ctx.add("assistant", action)
    ctx.add("user", small_obs)
    ctx.add("assistant", action)
    ctx.add("user", small_obs)
    ctx.add("assistant", action)
    print(f"  before the second read: tokens={ctx.total_tokens()} (budget {ctx.token_budget})")
    ctx.add("user", big_read, read_file_path="notes.md")  # second read of the SAME path
    print("  after the second read of notes.md (compaction fires inside this add()):")
    describe(ctx)
    ctx.add("assistant", action)
    ctx.add("user", small_obs)
    print("  two more turns later, no further compaction needed:")
    describe(ctx)


def demo_b_message_floor() -> None:
    print("\n=== Demo B: the floor of 3 holds even while still over budget ===")
    ctx = ContextManager(system_prompt="s" * 40, token_budget=30)  # system ~10 tok, tiny budget
    small_obs = "o" * 80  # ~20 tok, no read_file_path -- nothing to collapse
    for i in range(8):
        ctx.add("user" if i % 2 else "assistant", small_obs)
    print(f"  after 8 more turns against a {ctx.token_budget}-token budget with nothing collapsible:")
    describe(ctx)
    print(
        f"  final state is over budget ({ctx.total_tokens()} > {ctx.token_budget}) "
        f"but held at the floor of {len(ctx.messages)} messages -- the policy stops "
        "deleting rather than erase the model's last action and its own observation."
    )


if __name__ == "__main__":
    demo_a_collapse_before_drop()
    demo_b_message_floor()
