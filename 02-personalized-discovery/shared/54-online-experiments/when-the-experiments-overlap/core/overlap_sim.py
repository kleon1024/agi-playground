"""Two experiments share one traffic stream. Who measures what?

Stage 54's validity gate reads one experiment. This chapter asks the
platform question that has to be answered before the second experiment
starts: when two changes run on the same users, whose number is each
experiment's estimate?

The simulation holds one cohort of 20,000 users and one outcome, with a
known truth: experiment A moves the metric by 1.0, experiment B by 0.5,
and there is an interaction of 0.5 (when both treatments are on, the
effect is 2.0, not 1.5). Three platform behaviors produce three answers:

1. Naive shared bucket: both experiments hash the user with the same key
   and write to the same treatment flag, so assignment A is assignment B
   for every user. Each experiment's estimate comes out as
   A_effect + B_effect + interaction — the other team's change is fully
   inside your number, and both teams report the same lift.
2. Layered randomization (Tang, Agarwal, O'Brien and Meyer, 2010, KDD):
   each experiment owns a layer keyed to the user, hashed independently.
   Assignments are uncorrelated, so each estimate is the main effect
   averaged over the other experiment's states — unbiased, but the
   interaction is invisible to both single experiments.
3. A 2x2 factorial with four cells, from which A at B-off, B at A-off,
   and the interaction are read separately. This is the only design that
   sees the interaction.

Everything is deterministic: user ids hash with crc32, noise comes from a
seeded stdlib RNG, stdlib only.

Usage:
    uv run python core/overlap_sim.py
"""

from __future__ import annotations

import math
import random
import zlib

SEED = 7
N_USERS = 20_000
A_EFFECT = 1.0
B_EFFECT = 0.5
INTERACTION = 0.5
NOISE_SD = 2.0
THRESHOLD = 50
BASE = 100.0


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bucket(user_id: str, salt: str) -> int:
    """Deterministic 50/50 assignment: crc32 % 100 below the threshold."""
    h = zlib.crc32((salt + user_id).encode()) % 100
    return 1 if h < THRESHOLD else 0


def outcome(a: int, b: int) -> float:
    return BASE + A_EFFECT * a + B_EFFECT * b + INTERACTION * a * b


def estimate(assign: list[int], y: list[float]) -> tuple[float, float, float]:
    """Two-sample diff in means, Welch-style SE, two-sided normal p."""
    ys = [(a, v) for a, v in zip(assign, y)]
    t = [v for a, v in ys if a == 1]
    c = [v for a, v in ys if a == 0]
    mt, mc = sum(t) / len(t), sum(c) / len(c)
    vt, vc = sum((v - mt) ** 2 for v in t) / (len(t) - 1), sum(
        (v - mc) ** 2 for v in c
    ) / (len(c) - 1)
    se = math.sqrt(vt / len(t) + vc / len(c))
    z = (mt - mc) / se
    return mt - mc, se, 2.0 * (1.0 - norm_cdf(abs(z)))


def pearson(a: list[int], b: list[int]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return cov / math.sqrt(va * vb)


def main() -> None:
    rng = random.Random(SEED)
    users = [f"u{i}" for i in range(N_USERS)]
    noise = [rng.normalvariate(0.0, NOISE_SD) for _ in users]

    # Layered assignments: independent layers, the Tang et al. design.
    a_lay = [bucket(u, "layer-a:") for u in users]
    b_lay = [bucket(u, "layer-b:") for u in users]
    y_lay = [
        outcome(a, b) + nz for a, b, nz in zip(a_lay, b_lay, noise)
    ]

    # Naive shared bucket: both experiments write to the same flag.
    a_shared = [bucket(u, "shared:") for u in users]
    y_shared = [
        outcome(a, a) + nz for a, nz in zip(a_shared, noise)
    ]

    print("== 1. the truth ==")
    print(f"{N_USERS:,} users; A effect {A_EFFECT:g}, B effect "
          f"{B_EFFECT:g}, interaction {INTERACTION:g}, noise sd {NOISE_SD:g}")
    print("when both treatments are on, the metric moves by "
          f"{A_EFFECT + B_EFFECT + INTERACTION:g}, not "
          f"{A_EFFECT + B_EFFECT:g}.\n")

    print("== 2. naive shared bucket: one flag, two experiments ==")
    r = pearson(a_shared, a_shared)
    est_a, se_a, p_a = estimate(a_shared, y_shared)
    print(f"assignment correlation: {r:.2f} (identical by construction)")
    print(f"experiment A reports {est_a:.3f} (se {se_a:.3f}, p={p_a:.2g})")
    print(f"experiment B reports the same {est_a:.3f} — the two changes are")
    print("indistinguishable, and the estimate is A+B+interaction, not A.")
    print("the other team's effect is fully inside your number.\n")

    print("== 3. layered randomization: each experiment owns a layer ==")
    r = pearson(a_lay, b_lay)
    est_a, se_a, p_a = estimate(a_lay, y_lay)
    est_b, se_b, p_b = estimate(b_lay, y_lay)
    print(f"assignment correlation: {r:.3f} (independent layers)")
    print(f"experiment A reports {est_a:.3f} (se {se_a:.3f}, p={p_a:.2g}); "
          f"truth is A + interaction/2 = {A_EFFECT + INTERACTION / 2:.2f}")
    print(f"experiment B reports {est_b:.3f} (se {se_b:.3f}, p={p_b:.2g}); "
          f"truth is B + interaction/2 = {B_EFFECT + INTERACTION / 2:.2f}")
    print("each main effect is right, averaged over the other experiment's")
    print("50/50 rollout — and neither one sees the interaction.\n")

    print("== 4. the 2x2 factorial: the only design that sees the interaction ==")
    cells = {}
    for a in (0, 1):
        for b in (0, 1):
            vals = [
                outcome(a, b) + nz
                for aa, bb, nz in zip(a_lay, b_lay, noise)
                if aa == a and bb == b
            ]
            cells[(a, b)] = (len(vals), sum(vals) / len(vals))
    print(f"{'cell':>8} {'users':>8} {'mean':>8}")
    for a in (0, 1):
        for b in (0, 1):
            print(f"(A={a},B={b}) {cells[(a, b)][0]:>8,} "
                  f"{cells[(a, b)][1]:>8.3f}")
    a_b0 = cells[(1, 0)][1] - cells[(0, 0)][1]
    a_b1 = cells[(1, 1)][1] - cells[(0, 1)][1]
    b_a0 = cells[(0, 1)][1] - cells[(0, 0)][1]
    b_a1 = cells[(1, 1)][1] - cells[(1, 0)][1]
    inter = cells[(1, 1)][1] - cells[(1, 0)][1] - cells[(0, 1)][1] + cells[(0, 0)][1]
    print(f"\nA effect with B off:  {a_b0:.3f} (truth {A_EFFECT:g})")
    print(f"A effect with B on:   {a_b1:.3f} (truth "
          f"{A_EFFECT + INTERACTION:g})")
    print(f"B effect with A off:  {b_a0:.3f} (truth {B_EFFECT:g})")
    print(f"B effect with A on:   {b_a1:.3f} (truth "
          f"{B_EFFECT + INTERACTION:g})")
    print(f"interaction:          {inter:.3f} (truth {INTERACTION:g})")

    print("\n== 5. the verdict ==")
    print("the shared bucket is confident and wrong: a tight p-value on an")
    print("estimate that is not your change. Layering gives every experiment")
    print("its own unbiased main effect at the cost of interaction blindness;")
    print("when two changes touch the same funnel, only the factorial reads")
    print("the interaction — Tang et al. 2010 (KDD) for the layered design,")
    print("Kohavi et al. 2009 (DMKD 18(1)) for the interaction trade.")


if __name__ == "__main__":
    main()
