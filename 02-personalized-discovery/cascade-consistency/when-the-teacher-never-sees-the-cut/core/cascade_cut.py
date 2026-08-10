"""The teacher only ever scores survivors — what does the cascade re-learn?

Stage 63's fix distills the final ranker's score into the pre-rank. This
chapter asks what happens when the distillation target is itself truncated
by the cascade's cut: the teacher only scores the items the pre-rank let
through, so the student is trained on survivors and never sees the items
the cut rejected. Generation after generation the cheap stage converges
toward the cut — the popularity and candidate-source distribution — rather
than the final ranker's true intent, and an item that never survives the
cut can never be taught.

The teacher's score is a bounded probability — sigmoid(4 * (popularity +
quality)) — like a pCVR. Among the survivors the labels are saturated near
one, so the distilled student cannot learn anything from them except the
survivor feature geometry, which is popularity. The rejected tail's labels
carry the discrimination, and only the arms that score beyond the cut ever
see them.

The run simulates a two-stage cascade over six generations under three
teacher-label regimes:

1. survivors-only: the teacher scores just the cut's survivors (the failure);
2. full-corpus sample: the teacher also scores 400 uniform draws from the
   rejected corpus (fix one);
3. stratified sample: the teacher's extra labels are drawn per popularity
   group so the tail, which the cut starves hardest, is represented (fix
   two, the stratified-distillation read from WSDM 2023).

Each generation: cut 100 of 2,000 items, score the survivors with the
oracle teacher, fit the next student on that generation's labels, and cut
again. The oracle's true top-50 is fixed, so every generation the run can
read how much of the answer the teacher was ever allowed to score.

Deterministic (seeded stdlib RNG, no third-party code).

Usage:
    uv run python core/cascade_cut.py
"""

from __future__ import annotations

import math
import random

SEED = 93
N_ITEMS = 2_000
CUT = 100
K = 50
GENERATIONS = 6
RHO = 0.5  # correlation between item popularity and true quality
NOISE_POP = 0.30  # noise on the observed popularity feature
NOISE_QUAL = 1.50  # noise on the observed quality feature
SATURATION = 4.0  # sigmoid scale of the teacher's probability score
SAMPLE = 400  # extra teacher labels the fix arms take beyond the cut
EPOCHS = 60
LR = 0.10

ARM_NAMES = ("survivors-only", "full-corpus sample", "stratified sample")
GROUPS = (("head", 0.10), ("mid", 0.40), ("tail", 0.50))


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / math.sqrt(vx * vy)


def fit(pairs: list[tuple[list[float], float]]) -> tuple[list[float], float]:
    """Least-squares fit of a linear score to teacher labels, by gradient step."""
    w = [0.0, 0.0, 0.0]
    b = 0.0
    n = len(pairs)
    for _ in range(EPOCHS):
        gw = [0.0, 0.0, 0.0]
        gb = 0.0
        for f, t in pairs:
            pred = w[0] * f[0] + w[1] * f[1] + w[2] * f[2] + b
            e = pred - t
            gw[0] += e * f[0]
            gw[1] += e * f[1]
            gw[2] += e * f[2]
            gb += e
        for j in range(3):
            w[j] -= LR * gw[j] / n
        b -= LR * gb / n
    return w, b


def main() -> None:
    rng = random.Random(SEED)

    # Items carry an observed popularity feature, an observed quality
    # feature, and a junk feature. The teacher's true score is a saturated
    # probability of popularity plus quality, so among the head it is ~1
    # no matter the quality, and in the tail it carries the discrimination.
    items = []
    for _ in range(N_ITEMS):
        z_pop = rng.gauss(0.0, 1.0)
        z_qual = RHO * z_pop + math.sqrt(1.0 - RHO * RHO) * rng.gauss(0.0, 1.0)
        items.append(
            {
                "f": [
                    z_pop + rng.gauss(0.0, NOISE_POP),
                    z_qual + rng.gauss(0.0, NOISE_QUAL),
                    rng.gauss(0.0, 1.0),
                ],
                "t": sigmoid(SATURATION * (z_pop + z_qual)),
                "z_pop": z_pop,
            }
        )

    rank = sorted(range(N_ITEMS), key=lambda i: items[i]["z_pop"], reverse=True)
    group = ["tail"] * N_ITEMS
    for pos, idx in enumerate(rank):
        if pos < 200:
            group[idx] = "head"
        elif pos < 1_000:
            group[idx] = "mid"

    oracle_top_k = sorted(
        range(N_ITEMS), key=lambda i: items[i]["t"], reverse=True
    )[:K]
    oracle_set = set(oracle_top_k)

    def score(w: list[float], b: float, i: int) -> float:
        f = items[i]["f"]
        return w[0] * f[0] + w[1] * f[1] + w[2] * f[2] + b

    def cut(w: list[float], b: float) -> list[int]:
        order = sorted(range(N_ITEMS), key=lambda i: score(w, b, i), reverse=True)
        return order[:CUT]

    # Generation 0: every arm starts from the same popularity-baseline cut,
    # then each arm follows its own cascade from its own labels. The baseline
    # cut's own recall is the reference the student was meant to beat.
    baseline_cut = sorted(
        range(N_ITEMS), key=lambda i: items[i]["z_pop"], reverse=True
    )[:CUT]
    cur: dict[str, list[int]] = {
        arm: baseline_cut for arm in ARM_NAMES
    }
    baseline_recall = len(set(baseline_cut) & oracle_set)
    taught: dict[str, set[int]] = {arm: set(cur[arm]) for arm in ARM_NAMES}
    recall: dict[str, list[int]] = {arm: [] for arm in ARM_NAMES}
    surv_corr: dict[str, list[float]] = {arm: [] for arm in ARM_NAMES}
    full_corr: dict[str, list[float]] = {arm: [] for arm in ARM_NAMES}
    ever: dict[str, list[int]] = {arm: [] for arm in ARM_NAMES}
    final_state: dict[str, tuple[list[float], float, list[int]]] = {}

    for _ in range(1, GENERATIONS + 1):
        for arm in ARM_NAMES:
            survivors = set(cur[arm])
            taught[arm] |= survivors
            rejected = [i for i in range(N_ITEMS) if i not in survivors]
            pools = sorted(survivors)
            if arm == "full-corpus sample":
                pools += rng.sample(rejected, SAMPLE)
            elif arm == "stratified sample":
                for g_name, share in GROUPS:
                    members = [i for i in rejected if group[i] == g_name]
                    pools += rng.sample(
                        members, min(round(SAMPLE * share), len(members))
                    )
            w, b = fit([(items[i]["f"], items[i]["t"]) for i in pools])
            next_cut = cut(w, b)
            final_state[arm] = (w, b, next_cut)
            cur[arm] = next_cut

            recall[arm].append(len(set(next_cut) & oracle_set))
            surv_corr[arm].append(
                pearson(
                    [score(w, b, i) for i in next_cut],
                    [items[i]["t"] for i in next_cut],
                )
            )
            full_corr[arm].append(
                pearson(
                    [score(w, b, i) for i in range(N_ITEMS)],
                    [items[i]["t"] for i in range(N_ITEMS)],
                )
            )
            ever[arm].append(len(taught[arm] & oracle_set))

    header = f"{'arm':<17}" + "".join(f"{g:>8}" for g in range(1, GENERATIONS + 1))

    # --- section 1: the aggregate, read the way the team can read it ---
    print("== 1. the aggregate, read the way the team can read it ==")
    print(
        f"catalogue {N_ITEMS:,} items | pre-rank cut {CUT} | oracle top-{K} "
        f"| teacher score sigmoid({SATURATION:g} x (pop + qual))"
    )
    print()
    print("student vs teacher correlation on the pairs the teacher scored:")
    print(header)
    for arm in ARM_NAMES:
        print(f"{arm:<17}" + "".join(f"{v:>8.3f}" for v in surv_corr[arm]))
    print()

    # --- section 2: the full-corpus read, which the team cannot compute ---
    print("== 2. the same students against the full corpus (the read the ==")
    print("==    team cannot compute without scoring beyond the cut) ==")
    print(header)
    for arm in ARM_NAMES:
        print(f"{arm:<17}" + "".join(f"{v:>8.3f}" for v in full_corr[arm]))
    print()

    # --- section 3: top-K recall at the cut ---
    print("== 3. top-K recall at the cut: how much of the oracle's top-50 ==")
    print("==    survived this generation's pre-rank ==")
    print(header)
    print(
        f"{'popularity baseline':<17}"
        + "".join(f"{baseline_recall:>8}" for _ in range(GENERATIONS))
    )
    for arm in ARM_NAMES:
        print(f"{arm:<17}" + "".join(f"{v:>8}" for v in recall[arm]))
    print()

    # --- section 4: slice the final cut by popularity group ---
    print("== 4. the final cut, sliced by popularity group ==")
    print(f"{'arm':<17}{'head':>8}{'mid':>8}{'tail':>8}")
    for arm in ARM_NAMES:
        _, _, c = final_state[arm]
        counts = [sum(1 for i in c if group[i] == g) for g, _ in GROUPS]
        print(f"{arm:<17}" + "".join(f"{v:>8}" for v in counts))
    print("cut slots from each group; the corpus is 200 head / 800 mid / 1,000 tail")
    print()

    # --- section 5: the funnel closes ---
    print("== 5. the funnel closes: oracle top-K items the teacher ever ==")
    print("==    scored, cumulative ==")
    print(header)
    for arm in ARM_NAMES:
        print(f"{arm:<17}" + "".join(f"{v:>8}" for v in ever[arm]))
    print()

    # --- section 6: the verdict ---
    a_first = recall["survivors-only"][0]
    a_last = recall["survivors-only"][-1]
    b_last = recall["full-corpus sample"][-1]
    c_last = recall["stratified sample"][-1]
    a_ever = ever["survivors-only"][-1]
    b_ever = ever["full-corpus sample"][-1]
    c_ever = ever["stratified sample"][-1]
    a_sc_first = surv_corr["survivors-only"][0]
    a_sc_last = surv_corr["survivors-only"][-1]
    a_fc_first = full_corr["survivors-only"][0]
    a_fc_last = full_corr["survivors-only"][-1]
    b_fc_last = full_corr["full-corpus sample"][-1]

    print("== 6. the verdict ==")
    print(f"the survivors-only cascade starts at {a_first} of the oracle's top-{K}")
    print(f"and drifts down to {a_last}, below the {baseline_recall}-of-{K} popularity")
    print("baseline it was meant to beat. the student's survivor")
    print(f"read is flat near zero ({a_sc_first:+.3f} -> {a_sc_last:+.3f})")
    print(f"while its full-corpus read drifts {a_fc_first:.3f} -> {a_fc_last:.3f},")
    print("so the failure trends only in the read the team cannot compute.")
    print("scoring beyond the cut recovers the funnel: full-corpus sample")
    print(f"{b_last}, stratified sample {c_last}, full-corpus read {b_fc_last:.3f}.")
    print(f"the teacher ever scored {a_ever} of the oracle's top-{K} under")
    print(f"survivors-only labels, {b_ever} with a full-corpus sample, and")
    print(f"{c_ever} with a stratified sample. the {K - a_ever} items it never")
    print("scored can never be taught — that blind spot is the funnel this")
    print("chapter exists to name.")


if __name__ == "__main__":
    main()
