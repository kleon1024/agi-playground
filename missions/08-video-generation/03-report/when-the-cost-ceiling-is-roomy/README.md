---
status: verified
level: applied
base: scratch
label: When the cost ceiling is roomy
verified: 2026-08-06
---

# The feasibility verdict, read: quality margin and cost headroom

**Question:** [mission 08's report](../) is the feasibility verdict — the
generation must beat frame-repeat by more than its seed spread AND fit the
declared cost ceiling. This chapter recomputes the quality half from the
committed JSONs and reads the recorded cost half, so the verdict is one
table.

**Before this:** [mission 08's outcome report](../) and the frontier-grid
chapter.

## The verdict, recomputed

The run ([record](runs/2026-08-06-cost-report.md)) recomputes the quality
margin:

| | |
|---|---|
| LM completion per seed | 0.0804 / 0.0865 / 0.0882 |
| mean vs frame-repeat | 0.0851 vs 0.1281 |
| margin vs spread | 0.0430 vs 0.0078 (5.5x) |
| verdict | beats baseline outside seed noise |

Cost half (recorded): 152.5 / 150.6 / 153.9s total per seed, \$0, ceiling
1800s — **8.4-8.6% used**.

## Two readings

**The quality margin is decisive and the metric that rests on it is the
pixel one.** The margin (0.0430) is 5.5x the seed spread (0.0078) — the
generation beats frame-repeat outside seed noise. The exact-token match is
low (0.07-0.22), and the wrong-tokens chapter established why that is not
the verdict's metric: the codebook carries near-equivalent tokens, so the
pixel MSE is what the feasibility question depends on.

**The cost ceiling is roomy, and the pairing is the discipline.** The
mission uses 8.4-8.6% of its declared 1800s ceiling — the headroom is the
finding, not a footnote: video at this scale is affordable before the cost
question binds. And the report pairs cost with quality rather than
reporting either alone (mission.yaml's cost/quality-together rule), which
is the discipline the whole cost-first mission exists to enforce.

## Evidence boundary

The committed generation JSONs (quality, recomputed) and the recorded
report (cost, cited). It reads the verdict's two halves; it does not re-run
the training and does not extend the feasibility claim beyond the tested
scale.

## Check your mental model

Answer each before opening it.

**1. The exact-token match is 7-22%. Why does the report still call the
generation a pass?**

<details>
<summary>Answer</summary>

Because the acceptance metric is pixel MSE against the frame-repeat
baseline, not token identity. The generation's wrong tokens reconstruct at
0.0851 MSE, far below the 0.1281 baseline, because the codebook has
near-equivalent tokens for the same frame content. The report records the
exact-match caveat honestly — it is stage 01's codec ceiling, not a stage
02 failure — but the metric the verdict rests on is the pixel one.

</details>

**2. The mission used 8.5% of its cost ceiling. Why is that a finding and
not just a small number?**

<details>
<summary>Answer</summary>

Because the mission's central question is whether video is affordable at
all — before asking whether it is good. The 8.5% figure answers the prior
question with massive headroom: at this scale, the cost ceiling does not
bind, so the next question (longer sequences, more objects — the frontier
grid) is a quality question, not a compute question. The headroom is what
makes the frontier chapters' verdicts interpretable: they were never cost-
constrained.

</details>

## Next

Back to [mission 08's report](../), or to
[the frontier-grid chapter](../../06-longer-and-multi-object/when-the-metric-hits-zero/)
where the headroom gets spent on the harder corners.
