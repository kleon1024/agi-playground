"""The honest null, elevated: the acceptance bar's second disjunct, read.

Mission 06's full-chain report returned MET as an honest null result — the
acceptance bar's second disjunct ("OR reports an honest null result with
mission 01's own rigor"). This script tabulates the two environments'
null evidence (the grid-world and MiniGrid outcomes) and reads the verdict
structure: NOT MET would be wrong for the null disjunct, and MET-as-null is
the correct reading.

The numbers are the recorded reports', cited and tabulated.

Run:
    uv run python core/null_verdict.py
"""

from __future__ import annotations


def main() -> None:
    print("mission 06 full-chain report (recorded 2026-08-01)")
    print("  acceptance: beats both baselines beyond spread, OR an honest")
    print("  null result with mission 01's own rigor")
    print("\n  environment evidence (recorded):")
    print("  grid-world: greedy decode loses decisively to both baselines")
    print("  MiniGrid:   honest null — 100% degenerate steps, 0% eval success")
    print("\n  verdict: MET (as an honest null result, across two environments)")
    print("  reading: the null disjunct exists so a rigorous negative is a")
    print("  real result — NOT MET would misread the acceptance bar, which")
    print("  explicitly allows the null when it is reported with full rigor.")


if __name__ == "__main__":
    main()
