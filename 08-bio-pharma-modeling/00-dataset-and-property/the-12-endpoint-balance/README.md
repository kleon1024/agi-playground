---
status: verified
level: applied
base: scratch
label: The 12-endpoint balance
verified: 2026-08-06
---

# Why the endpoint was chosen from balance, not convenience

**Question:** [stage 00's dataset](../) picked one of 12 Tox21 endpoints.
This chapter reads the recorded balance table and asks why the choice was
made before any model saw the data.

**Before this:** [stage 00's dataset and property](../) and its recorded
run.

## The table, read

The run ([record](runs/2026-08-06-balance-read.md)) reads the recorded
balance for all 12 endpoints. The extremes:

| endpoint | positive rate |
|---|---:|
| NR-PPAR-gamma | 2.9% (most imbalanced) |
| NR-ER | 12.8% |
| **SR-MMP** | **15.8% (chosen)** |
| SR-ARE | 16.2% (near-duplicate of SR-MMP) |

## Two readings

**The choice is made from balance and assay semantics before any model
sees the data.** SR-MMP is the best-balanced endpoint (15.8%, tied with
SR-ARE) and its assay has a single statable mechanism — loss of
mitochondrial membrane potential — which makes "what does this label
measure" answerable in one sentence. SR-ARE's antioxidant-response-element
reporter is broader and less specific. The choice is made once, here, per
the guardrail against choosing after seeing which endpoint flatters a
result.

**The balance table is the audit trail for every later comparison.** The
12 rates are computed directly from the downloaded CSV, not estimated, and
recorded before stage 01 trains anything. That is what makes the
cross-endpoint analysis (stages 03-05) meaningful: the imbalance
spectrum is fixed in advance, so the scarcity-variance pattern was not
reverse-engineered from which endpoint won.

## Evidence boundary

The recorded dataset run (Tox21 CSV, 12 endpoints, one download). It reads
that artifact; it does not re-download and the rates characterize this
panel's labels.

## Check your mental model

Answer each before opening it.

**1. Why is SR-ARE rejected if it is the best-balanced endpoint too?**

<details>
<summary>Answer</summary>

Because balance alone is not the criterion. SR-ARE's 16.2% matches
SR-MMP's 15.8%, but its assay measures a broader, less specific stressor
response — so "what does the label mean" is not answerable in one
sentence. SR-MMP's single statable mechanism is what makes the endpoint
interpretable, and the choice combines balance with semantics.

</details>

**2. What does recording the table before training buy?**

<details>
<summary>Answer</summary>

It fixes the comparison's axes in advance. The 12 rates are the imbalance
spectrum the cross-endpoint analysis later reads; recording them before
any model result means the endpoint choices and their rationales cannot
be adjusted to flatter a finding. The audit trail is what makes the
mission's scarcity pattern a result rather than a post-hoc story.

</details>

## Next

Back to [stage 00](../), or to
[does the split decide who wins](../the-split-that-decides/) which reads
the same stage's split story.
