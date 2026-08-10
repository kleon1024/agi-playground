"""The annealed mix moves the evals, measured as a two-skill seesaw.

The mid-training mix decision is a multi-objective trade wearing the
clothes of a pipeline detail. Raising the agentic share in the annealing
window raises the agentic eval and lowers the general eval, and the two
curves trade differently depending on which slice you watch. This script
builds the seesaw explicitly: an anneal window of 20,000 docs, a declared
agentic share s, and two skill axes whose exposure the window teaches.

Agentic skill saturates, A(s) = 1 - exp(-40s): the first points of share
buy most of the capability, and past roughly 8 percent each additional
point buys less than the general-eval point it displaces.

General skill loses with a recency multiplier, G(s) = 1 - 1.6s: displaced
general tokens in the final window hurt more than uniform displacement,
because annealed tokens dominate the final checkpoint.

The audit sweeps s from 0 to 10 percent, prints the two eval curves and
their marginal trade, and asks whether a blended aggregate can see the
seesaw at all. It cannot: the blended number keeps rising past the point
where the general slice breaches the guardrail, which is why the slice
read is the case-finding step and the aggregate is the failure mode.

Run:
    uv run python core/mix_seesaw.py
"""

from __future__ import annotations

import math
from itertools import pairwise

ANNEAL_DOCS = 20_000
SHARES = (0.00, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10)
AGENTIC_RATE = 40.0
RECENCY_MULTIPLIER = 1.6
GUARDRAIL_DELTA = 0.10


def agentic_eval(share: float) -> float:
    """Fraction of the agentic capability the window installed."""
    return 1.0 - math.exp(-AGENTIC_RATE * share)


def general_eval(share: float) -> float:
    """Fraction of the general capability that survives displacement."""
    return 1.0 - RECENCY_MULTIPLIER * share


def main() -> None:
    print(
        f"anneal window: {ANNEAL_DOCS:,} docs; sweep s = 0..10% agentic "
        "share"
    )
    print(
        f"agentic skill A(s) = 1 - exp(-{AGENTIC_RATE:.0f}s); general skill "
        f"G(s) = 1 - {RECENCY_MULTIPLIER:.1f}s (annealed displacement weighs "
        "more than uniform)"
    )
    print(
        f"guardrail: general eval >= baseline - {GUARDRAIL_DELTA:.0%}"
    )
    print()
    print(
        "share   agentic  general  blended  general-delta   verdict"
    )

    baseline_general = general_eval(0.0)
    guardrail = baseline_general - GUARDRAIL_DELTA
    breaches = []
    blends = []
    for share in SHARES:
        a = agentic_eval(share)
        g = general_eval(share)
        blended = 0.5 * (a + g)
        delta = g - baseline_general
        breach = g < guardrail
        blends.append(blended)
        if breach:
            breaches.append(share)
        verdict = "GUARDRAIL BREACH" if breach else "within guardrail"
        print(
            f"{share:5.2f}   {a:7.3f}  {g:7.3f}  {blended:7.3f}  "
            f"{delta:+8.3f}   {verdict}"
        )

    print()
    print("marginal trade, per point of share (share -> next share):")
    print("  from     to   dA/pt   dG/pt   agentic still pays?")
    for prev, nxt in pairwise(SHARES):
        step = nxt - prev
        d_a = (agentic_eval(nxt) - agentic_eval(prev)) / step
        d_g = (general_eval(nxt) - general_eval(prev)) / step
        pays = "yes" if d_a > -d_g else "no -- the trade has flipped"
        print(
            f"  {prev:5.2f}  {nxt:5.2f}  {d_a:6.2f}  {d_g:6.2f}   {pays}"
        )

    knee = next(
        (nxt for prev, nxt in pairwise(SHARES)
         if (agentic_eval(nxt) - agentic_eval(prev)) / (nxt - prev)
         <= -(general_eval(nxt) - general_eval(prev)) / (nxt - prev)),
        None,
    )

    print()
    if breaches:
        first_breach = breaches[0]
        safe_blend = blends[SHARES.index(0.05)]
        breach_blend = blends[SHARES.index(first_breach)]
        print(
            f"verdict: the general slice breaches its guardrail at s = "
            f"{first_breach:.2f}, before the agentic eval saturates "
            f"(agentic {agentic_eval(first_breach):.3f} of a saturating "
            "curve). The marginal"
        )
        if knee is not None:
            print(
                f"trade flips between s = {SHARES[SHARES.index(knee)-1]:.2f} "
                f"and s = {knee:.2f}: each point of agentic share buys "
                f"{abs(agentic_eval(knee) - agentic_eval(SHARES[SHARES.index(knee)-1])) / 0.02:.2f} "
                "of agentic eval against a 1.60 general-eval cost, so past "
                "the knee the trade no longer pays. The blended"
            )
        else:
            print(
                "trade still pays at the top of the swept range, so the "
                "breach is a guardrail decision, not a knee. The blended"
            )
        print(
            f"number rises through the breach ({safe_blend:.3f} at s = 0.05 "
            f"to {breach_blend:.3f} at s = {first_breach:.2f}), so an "
            "aggregate-only read rewards exactly the move that breaks the "
            "contract -- the slice read is the case-finding step."
        )
    else:
        print(
            "verdict: no swept share breaches the general guardrail; the "
            "seesaw is real but stays inside the contract across the range."
        )


if __name__ == "__main__":
    main()
