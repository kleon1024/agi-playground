---
status: verified
level: applied
base: scratch
label: The variance that decides
verified: 2026-08-06
---

# A headline win that still loses, seed by seed

**Question:** [stage 09's report](../) rejects a positive mean gap not
larger than its 95% margin. This chapter reads the breached fixture's
seed-level arrays and asks what the variance math actually decides.

**Before this:** [stage 09's report](../) and its breached fixture.

## The variance, read

The run ([record](runs/2026-08-06-variance-read.md)) reads the fixture's
five seeds:

| arm | per-seed nDCG@10 | spread |
|---|---:|---:|
| candidate | 0.412, 0.398, 0.421, 0.405, 0.415 | 0.0230 |
| popularity | 0.301, 0.309, 0.295, 0.303, 0.298 | 0.0140 |
| item-item CF | 0.356, 0.348, 0.362, 0.351, 0.359 | 0.0140 |

Candidate mean gap vs CF: +0.0550 — beyond the candidate's own spread.

## Two readings

**The headline is real by the mission's own rule.** The candidate beats
both baselines by more than its seed spread (0.0550 vs 0.0230), which is
the "a gap smaller than run-to-run spread is no result" bar — so the
positive finding is not a lucky seed. The five seeds are what make that
claim: one seed would be a coin flip, five narrow the uncertainty into a
margin the evaluator can check.

**The verdict is still NOT MET, and the variance is why the guardrail
outranks the headline.** The cold-start guardrail fell below its baseline
(0.271 vs 0.298). The report treats variance as a veto input: the seed
spread decides whether a gap counts, and the guardrail decides whether the
mission passes — neither is an appendix, and the fixture renders both in
one table so the headline cannot be read without the veto.

## The fix and its trade

The fix is to require at least five seeds and to reject any positive mean
gap not larger than its uncertainty margin — variance is a veto input, not
an appendix. The fixture's seed arrays price the rule: the candidate's
per-seed spread is 0.0230 and its gap to item-item CF is +0.0550, so the
headline is real by the mission's own rule; one seed would be a coin flip,
five narrow the uncertainty into a margin the evaluator can check. The
verdict is still NOT MET because the cold-start guardrail (0.271 versus
0.298) is a veto that outranks the headline.

The trade, named: multi-seed evaluation costs compute — every arm must be
run five times, and the cost lands on the model team — and the margin
rule rejects real but noisy wins that a single run would have certified.
The report's rendering discipline is the other half: variance and the
guardrail are both inputs to the same verdict, so a win that does not clear
its own spread is reported as NOT MET, and a win that clears its spread
but breaches a guardrail is reported as NOT MET for a different reason.

## Who owns the loop

- **The evaluation team** owns the seed-level reporting and the margin
  rule — the normal-approximation spread comparison is a readable teaching
  choice, not a substitute for a test matched to a real experiment's
  dependence structure.
- **Each stage owner** owns running the required number of seeds and
  recording them with command, revision, split, and environment.
- **The product owner** owns the guardrail that outranks the headline —
  the veto is a mission promise, not an evaluator preference.

## Evidence boundary

The committed breached fixture (explicitly synthetic and illustrative —
it demonstrates the report format and the veto rule, not a mission result).
It reads that artifact; it does not change the mission's current CANNOT
DETERMINE status.

## Check your mental model

Answer each before opening it.

**1. Why does the evaluator compare the gap to the spread rather than to
zero?**

<details>
<summary>Answer</summary>

Because zero is not the right null. The candidate's score varies seed to
seed (spread 0.0230), so a small positive gap could be pure sampling noise.
The rule "gap must exceed run-to-run spread" (or its 95% margin) is what
distinguishes a real difference from a lucky draw. The five seeds are what
make the spread a number instead of a guess.

</details>

**2. What would a report that hid the guardrail have said?**

<details>
<summary>Answer</summary>

It would have reported the headline — candidate beats both baselines — and
let the cold-start regression pass unread. The report renders the breach in
the same output as the win, which is the only ordering that makes the veto
unmissable. A headline with a broken promise is a loss by the mission's own
contract, and the fixture exists to show that reading.

</details>

## Next

Back to [stage 09's report](../), or to
[the guardrail that vetoes a headline](../when-the-guardrail-vetoes/) which
reads the same fixture's veto side.
