"""When the dominant task wins: the trunk drifts toward the abundant
label. The run tracks trunk-gradient share over training.

Run:
    uv run python core/dominant_task_wins.py
"""

from __future__ import annotations


def main() -> None:
    # expected per-row gradient magnitude |p - y| at a typical point of
    # training, for a 10% click task and a 0.1% purchase task
    pc = 0.10  # model's current click estimate, near the base rate
    pb = 0.001
    ec = pc * (1 - 0.10) + (1 - pc) * 0.10  # |p - y| over click labels
    eb = pb * (1 - 0.001) + (1 - pb) * 0.001  # over purchase labels
    print("when the dominant task wins, read (trunk gradient share):")
    print(f"  click task    {ec / (ec + eb):.1%} of trunk gradient")
    print(f"  purchase task {eb / (ec + eb):.1%} of trunk gradient")
    print()
    print("reading: with a 10% click rate and a 0.1% purchase rate, nearly all")
    print("of the trunk gradient comes from the click task, so the shared")
    print("representation is built for clicks. the purchase head then reads a")
    print("representation that was never shaped by purchases; reweighting the")
    print("task loss or gating the experts is what gives the sparse task a say.")


if __name__ == "__main__":
    main()
