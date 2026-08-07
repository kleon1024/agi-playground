"""Interleaving credit, audited: does the blend decide the winner?

Stage 38 compares two rankings by blending them and crediting clicks to
the team that proposed each clicked result. This script asks whether
the credit is biased by position: users click whatever sits near the
top regardless of quality, so a blend that gives one team better
positions credits clicks that team did not earn.

Run:
    uv run python core/interleave_position.py
"""

from __future__ import annotations

import random

# Position click probabilities, declared: the first slot is clicked far
# more often than the sixth, independent of what sits there.
POSITION_PROBS = (0.30, 0.20, 0.14, 0.10, 0.07, 0.05)

# Team proposals are disjoint on purpose: with no shared document, every
# click's credit is unambiguous and any imbalance in the credited share
# comes from the blend, not from a tie rule.
TEAM_A = ("d1", "d3", "d5")
TEAM_B = ("d2", "d4", "d6")


def blend(a_start: bool) -> list[str]:
    """Round-robin blend of the two proposals, starting from one team."""
    if a_start:
        return ["d1", "d2", "d3", "d4", "d5", "d6"]
    return ["d2", "d1", "d4", "d3", "d6", "d5"]


def simulate(sessions: int, seed: int, always_a_start: bool) -> dict[str, float]:
    """Run sessions; return the share of clicked sessions each team won."""
    rng = random.Random(seed)
    credits = {"team_a": 0, "team_b": 0, "no_click": 0}
    for _ in range(sessions):
        if always_a_start:
            a_start = True
        else:
            a_start = rng.random() < 0.5
        shown = blend(a_start)
        click_pos = rng.choices(
            range(7), weights=POSITION_PROBS + (1.0 - sum(POSITION_PROBS),)
        )[0]
        if click_pos == 6:
            credits["no_click"] += 1
        elif shown[click_pos] in TEAM_A:
            credits["team_a"] += 1
        else:
            credits["team_b"] += 1
    total = sessions - credits["no_click"]
    return {
        "team_a": credits["team_a"] / total,
        "team_b": credits["team_b"] / total,
        "no_click": credits["no_click"] / sessions,
    }


def main() -> None:
    sessions = 10_000
    print("interleaving credit, audited: does the blend decide the winner?")
    print(f"  sessions: {sessions} (fixed seed); position click probs:")
    print("    positions 1-6:", " ".join(f"{p:.2f}" for p in POSITION_PROBS))
    print("  team A proposes", ", ".join(TEAM_A), "| team B proposes",
          ", ".join(TEAM_B))
    print()

    naive = simulate(sessions, 7, always_a_start=True)
    balanced = simulate(sessions, 7, always_a_start=False)

    print("naive blend (team A starts every session):")
    print(f"  credited share: team A {naive['team_a']:.1%}, "
          f"team B {naive['team_b']:.1%}")
    print(f"  sessions without a click: {naive['no_click']:.1%}")
    print("balanced blend (random start per session):")
    print(f"  credited share: team A {balanced['team_a']:.1%}, "
          f"team B {balanced['team_b']:.1%}")
    print(f"  sessions without a click: {balanced['no_click']:.1%}")
    print()

    print("reading: the teams are equal, so the difference is the blend.")
    print("The naive A-start list puts A at positions 1, 3, 5, whose")
    print("click probs sum to 0.51, and B at 2, 4, 6 (0.35). The audit")
    print(f"measures the result: A is credited {naive['team_a']:.1%} of")
    print(f"clicked sessions against {naive['team_b']:.1%} for B. Random")
    print(f"start averages the two lists and lands at {balanced['team_a']:.1%}/"
          f"{balanced['team_b']:.1%}. The fix is the random start, and the")
    print("trade is variance: each session flips, so the experiment needs")
    print("more sessions to see a real difference (Chapelle et al., 2012,")
    print("TOIS; Joachims et al., 2005, SIGIR; Radlinski & Craswell,")
    print("2010, SIGIR).")


if __name__ == "__main__":
    main()
