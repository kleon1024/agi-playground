"""Evaluation-gated release: the mechanism, not a claim about real model safety.

A gate takes a candidate release's scores on a fixed eval suite, applies a
declared threshold rule, and returns PASS or BLOCK plus the reasons. Every
score here is synthetic (`generate_synthetic_candidates`) -- there is no real
model or real capability being measured. What this script demonstrates is
the one thing every real eval-gate framework has in common underneath its
specific eval suite: a numeric rule computed the same way every time, and the
false-positive/false-negative tradeoff that rule cannot escape.

Two commands:
  demo  -- walk one candidate through the gate and show the reasons.
  sweep -- vary the category ceiling and show how many synthetically-labeled
           "actually unsafe" candidates pass, and how many "actually safe"
           candidates get blocked, at each threshold. This is the mechanism
           that makes "pick a good threshold" a policy decision, not a
           measurement one: tightening the ceiling always trades one error
           type for the other, it never removes both at once.
"""

import argparse
import random

CATEGORIES = ["cbrn_uplift", "cyber_uplift", "persuasion", "autonomous_replication"]


def generate_synthetic_candidates(n, seed):
    """Each candidate gets a hidden `true_risk` in [0, 1] and a per-category
    observed score = true_risk + independent measurement noise, clipped to
    [0, 1]. `true_unsafe` is a declared ground-truth label (true_risk > 0.7)
    that only exists because this data is synthetic -- a real eval has no
    such oracle, which is exactly why the sweep below matters.
    """
    rng = random.Random(seed)
    candidates = []
    for i in range(n):
        true_risk = rng.random()
        scores = {}
        for cat in CATEGORIES:
            noise = rng.gauss(0, 0.08)
            scores[cat] = min(1.0, max(0.0, true_risk + noise))
        candidates.append(
            {
                "id": f"candidate-{i:04d}",
                "true_risk": true_risk,
                "true_unsafe": true_risk > 0.7,
                "scores": scores,
            }
        )
    return candidates


def evaluate_gate(scores, baseline_scores, category_ceiling, aggregate_delta_ceiling):
    """The gate rule: block if ANY category exceeds its ceiling, OR if the
    aggregate (mean across categories) rises more than `aggregate_delta_ceiling`
    over the declared baseline release. Returns (decision, reasons).
    """
    reasons = []
    for cat, val in scores.items():
        if val > category_ceiling:
            reasons.append(f"{cat}={val:.3f} exceeds ceiling {category_ceiling:.3f}")

    aggregate = sum(scores.values()) / len(scores)
    baseline_aggregate = sum(baseline_scores.values()) / len(baseline_scores)
    delta = aggregate - baseline_aggregate
    if delta > aggregate_delta_ceiling:
        reasons.append(
            f"aggregate {aggregate:.3f} rose {delta:.3f} over baseline "
            f"{baseline_aggregate:.3f}, exceeds allowed delta {aggregate_delta_ceiling:.3f}"
        )

    decision = "BLOCK" if reasons else "PASS"
    return decision, reasons


def sweep_aggregate_deltas(candidates, deltas, category_ceiling, baseline_scores):
    """Hold the per-category ceiling disabled (above any reachable score) and
    vary only the aggregate-delta-over-baseline threshold. Isolating one rule
    at a time is what makes the tradeoff visible: with both rules active, the
    stricter one silently sets the floor and the other's sweep looks flat
    (see the README for the two-rule version of this same candidate set,
    which is exactly the number this isolated sweep explains).
    For each threshold, gate every candidate and count:
    - false_block: true_unsafe is False but the gate says BLOCK
    - false_pass:  true_unsafe is True  but the gate says PASS
    Both are computed against the SAME candidate set at every threshold, so
    the only thing changing row to row is the rule's strictness.
    """
    rows = []
    for delta in deltas:
        false_block = 0
        false_pass = 0
        n_unsafe = 0
        n_safe = 0
        for c in candidates:
            decision, _ = evaluate_gate(
                c["scores"], baseline_scores, category_ceiling, delta
            )
            if c["true_unsafe"]:
                n_unsafe += 1
                if decision == "PASS":
                    false_pass += 1
            else:
                n_safe += 1
                if decision == "BLOCK":
                    false_block += 1
        rows.append(
            {
                "delta_ceiling": delta,
                "false_block_rate": false_block / n_safe if n_safe else 0.0,
                "false_pass_rate": false_pass / n_unsafe if n_unsafe else 0.0,
                "n_safe": n_safe,
                "n_unsafe": n_unsafe,
            }
        )
    return rows


def cmd_demo(args):
    candidates = generate_synthetic_candidates(args.n, args.seed)
    baseline_scores = {cat: 0.35 for cat in CATEGORIES}
    picked = candidates[args.candidate_index]
    print(f"candidate: {picked['id']}  true_risk={picked['true_risk']:.3f} "
          f"true_unsafe={picked['true_unsafe']}")
    print("scores:", {k: round(v, 3) for k, v in picked["scores"].items()})
    decision, reasons = evaluate_gate(
        picked["scores"], baseline_scores, args.category_ceiling, args.aggregate_delta_ceiling
    )
    print(f"decision: {decision}")
    for r in reasons:
        print(f"  reason: {r}")
    if not reasons:
        print("  reason: no category exceeded its ceiling, aggregate delta within bound")


def cmd_sweep(args):
    candidates = generate_synthetic_candidates(args.n, args.seed)
    baseline_scores = {cat: 0.35 for cat in CATEGORIES}
    deltas = [round(0.05 + 0.05 * i, 2) for i in range(13)]
    rows = sweep_aggregate_deltas(candidates, deltas, args.category_ceiling, baseline_scores)
    n_unsafe = rows[0]["n_unsafe"]
    n_safe = rows[0]["n_safe"]
    print(f"n_candidates={args.n} n_unsafe={n_unsafe} n_safe={n_safe}")
    print(f"{'delta_ceiling':>13} {'false_block_rate':>17} {'false_pass_rate':>17}")
    for row in rows:
        print(
            f"{row['delta_ceiling']:>13.2f} {row['false_block_rate']:>17.3f} "
            f"{row['false_pass_rate']:>17.3f}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Gate one synthetic candidate and show reasons")
    demo.add_argument("--n", type=int, default=200)
    demo.add_argument("--seed", type=int, default=0)
    demo.add_argument("--candidate-index", type=int, default=0)
    demo.add_argument("--category-ceiling", type=float, default=0.70)
    demo.add_argument("--aggregate-delta-ceiling", type=float, default=0.15)
    demo.set_defaults(func=cmd_demo)

    sweep = sub.add_parser(
        "sweep", help="Sweep the aggregate-delta threshold and report the tradeoff"
    )
    sweep.add_argument("--n", type=int, default=2000)
    sweep.add_argument("--seed", type=int, default=0)
    sweep.add_argument("--category-ceiling", type=float, default=1.10)
    sweep.set_defaults(func=cmd_sweep)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
