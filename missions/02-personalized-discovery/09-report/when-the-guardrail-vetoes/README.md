---
status: verified
level: applied
base: scratch
label: When the guardrail vetoes
verified: 2026-08-06
---

# A headline win that is still NOT MET

**Question:** [stage 09's report](../) treats guardrails as vetoes, not
extra points. The breached fixture is the sharpest demonstration: the
candidate beats both baselines on nDCG@10 by more than seed variance, and
the verdict is still NOT MET. This chapter reads the fixture and shows why.

**Before this:** [stage 09's report](../), and the report format's three-way
verdict (MET / NOT MET / CANNOT DETERMINE).

## The veto, read

The run ([record](runs/2026-08-06-guardrail-veto.md)) reads the committed
fixture:

| metric | candidate | baseline | reading |
|---|---:|---:|---|
| nDCG@10 vs popularity | 0.4102 | 0.3012 | beats by > seed variance |
| nDCG@10 vs item-item CF | 0.4102 | 0.3552 | beats by > seed variance |
| cold-start coverage | 0.271 | 0.298 | **BREACH** |

## Two readings

**A guardrail is a veto, not an extra point.** The candidate wins the
headline comparison — both baselines, beyond seed variance — and the
verdict is still NOT MET, because the cold-start guardrail fell below its
baseline. The report renders both in the same output so the headline cannot
be read without the veto. A system that improves the average while taxing
new users has not improved personalization; it has found a different way to
be unfair, and the guardrail exists to say so.

**The veto is on the slice the mission exists to serve.** The breached
guardrail is cold-start coverage — new users with fewer than five
interactions, exactly the people personalization is supposed to help. That
is not an arbitrary gate; it is the mission's own promise about whom the
system helps, and the report refuses to let a higher average hide a
regression on that promise.

## Evidence boundary

The committed synthetic fixture (explicitly illustrative — it demonstrates
the report format and the veto rule, not a mission result). It reads the
fixture and does not change the mission's current `CANNOT DETERMINE`
status, which stage 09 itself states is the only honest conclusion until a
real integrated run emits the required artifact.

## Check your mental model

Answer each before opening it.

**1. The candidate beats both baselines decisively. Why does the chapter
call the outcome a failure?**

<details>
<summary>Answer</summary>

Because the mission contract makes guardrails vetoes, not extra points. The
headline win answers "is the model better on average?" — and the guardrail
answers "is it better for the people it is supposed to help?" Cold-start
coverage regressed below its baseline, so the answer to the second question
is no. A higher average with a broken promise is a loss, by the contract
declared before any code existed.

</details>

**2. Why does the cold-start slice matter more than the headline metric?**

<details>
<summary>Answer</summary>

Because the slice is the mission's purpose. Personalization exists to help
users without history; if the system makes that slice worse, it has
delivered the opposite of its promise, no matter what the aggregate says.
The aggregate can always be improved by serving the head — that is exactly
the failure the guardrail prevents.

</details>

## Next

Back to [stage 09's report](../), which also shows the honest default —
`CANNOT DETERMINE` when the required artifact does not exist.
