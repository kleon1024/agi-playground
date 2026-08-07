---
status: verified
level: applied
base: scratch
label: When the incrementality is zero
verified: 2026-08-07
---

# Zero lift is the null result measurement exists to find

**Question:** [stage 30's ads measurement](../) measures the ad by what
it changed. This chapter reads the executed null-result case and asks
why reporting it is the point of the discipline.

**Before this:** [stage 30 — ads measurement](../) and its executed
incrementality model.

## The null, executed

The run ([record](runs/2026-08-07-zero-lift-read.md)) compares exposed
and control on one campaign:

| group | conversion rate |
|---|---:|
| exposed | 0.030 |
| control | 0.030 |
| lift | +0.0% |

## The reading

The campaign delivered millions of impressions and changed nothing —
every click it got would have happened without it. Zero lift is the
null result measurement exists to find; a report that hides it is
crediting spend with no effect. The exposed group's 0.030 looks like
performance until the control group's identical 0.030 says the campaign
was noise. Reporting the zero is how the measurement protects the next
budget decision.

## The fix and its trade

The fix is to make the null result the reporting default: the campaign
is reported by its increment and its confidence interval, and a lift
smaller than the CI is reported as "cannot distinguish from zero,"
exactly what [the too-small-to-see detour](../when-the-lift-is-too-small-to-see/)
computes (at 10,000 users per arm the half-width of 0.47 points is
wider than the 0.4-point increment itself). The trade is that a strict
null default reads as failure in a channel whose job is to show
results — campaigns with genuinely small increments get killed, which
is the correct call for the budget but the uncomfortable one for the
platform that wants to keep the spend (Blake, Nosko & Tadelis, 2015,
Econometrica, found eBay's search ads drove far less incremental sales
than the ad spend — the real-world zero-lift case). The alternative —
hide the null and report the observed clicks — is the failure the
detour measures: the report credits spend with no effect.

## Evidence boundary

The executed comparison over two declared rates (illustrative,
deterministic). It demonstrates the null case; real incrementality
experiments report confidence intervals, and a small observed lift
against a wide interval is the same result in statistical form.

## Check your mental model

Answer each before opening it.

**1. Why does the exposed group's conversion rate prove nothing here?**

<details>
<summary>Answer</summary>

Because the control group converted at the same rate. The exposed
group's 0.030 is not evidence of the ad's effect — it is the baseline
rate the population would have had anyway. The increment is the
difference between the two, and the difference is zero. Without the
control, the same number would have been reported as success.

</details>

**2. What does a zero-lift report protect?**

<details>
<summary>Answer</summary>

The next budget decision. If the zero is hidden, the campaign looks
successful and spend continues on an effect that does not exist. If it
is reported, the advertiser can reallocate — the null result is the
measurement's value, and suppressing it converts a measurement failure
into a spend error.

</details>

## Next

Back to [stage 30](../), which closes the ads track. The
[attribution detour](../when-attribution-overcounts/) shows the
model-side overcount that the same control-group discipline corrects.
