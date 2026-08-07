"""When gating does not help: if the tasks are near-duplicates, the
MMoE gate collapses to one expert and the added parameters buy nothing.

Run:
    uv run python core/gating_no_help.py
"""

from __future__ import annotations


def main() -> None:
    # gate weights: task 0 and task 1 both put all mass on expert 0
    print("when gating does not help, read (gate collapse):")
    print("  task 0 gate: expert0 0.99, expert1 0.01")
    print("  task 1 gate: expert0 0.98, expert1 0.02")
    print("  effective: one expert, two copies of the same trunk")
    print()
    print("reading: MMoE pays off when tasks disagree about which expertise")
    print("they need — different features, different regimes. when both tasks")
    print("want the same representation, the gate collapses to a single expert")
    print("and the architecture is a shared bottom with extra parameters and")
    print("more serving cost. the diagnostic is to look at the learned gate")
    print("weights and the per-task gain over a plain shared bottom before")
    print("committing to gating.")


if __name__ == "__main__":
    main()
