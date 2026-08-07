---
status: verified
level: applied
base: scratch
label: When the counter drifts
verified: 2026-08-08
---

# The cap reads a counter that can reset underneath it

**Question:** [stage 25's frequency capping](../) caps by exposure
count. This chapter reads the executed counter-drift audit and asks
what happens when the counter — an identity object — is lost and the
cap starts over.

**Before this:** [stage 25 — frequency capping](../) and its executed
decay model, and [stage 17 — budget pacing](../../17-budget-pacing/)
for the delivery loop the counter lives in.

## The drift, executed

The run ([record](runs/2026-08-08-counter-drift.md)) serves 10,000
users (fixed seed) with the stage's decay curve, cap 3, and identity
failures: 25 percent of users lose their counter once, 5 percent twice,
at random true exposures inside the cap range:

| campaign | impressions | exp. clicks | clicks/imp | dead share |
|---|---:|---:|---:|---:|
| correct counter | 30,000 | 1,200.0 | 0.0400 | 0.0% |
| counter drift | 36,167 | 1,285.6 | 0.0355 | 3.1% |

Extra impressions served: 6,167. Extra expected clicks: +85.6 (+7.1%).

## The failure mode, named

**The counter is an identity object, and identity breaks.** The cap is
enforced on a counter keyed to a cookie, an app install id, or a
logged-in user id. When that object resets — cookie cleared, browser
switched, second device — the counter returns to zero and the cap
starts over, so the same human is served again. The audit's numbers are
the symptom: 6,167 extra impressions delivered at about one-third of
the first-three click value (0.0139 on the extra impressions versus
0.0400), and the dead share — impressions served at or below 0.005 CTR
— rises from 0.0 to 3.1 percent. The advertiser pays for impressions
that were supposed to be capped, and the user's tolerance is spent on
an ad they have already stopped clicking.

**The aggregate looks fine while the over-serve compounds.** The
clicks-per-impression column falls only from 0.0400 to 0.0355, so a
campaign-level CTR report barely moves; the failure is invisible until
the serving log is joined to a stable identity and the extra exposures
are counted. Finding the case means measuring delivered exposure per
stable human, not per counter — the same stratification discipline the
stage's hidden-slice audit applies to segments, applied to identity.

**A reset counter is censored exposure, not zero.** The cap cannot tell
a user who is genuinely new from a user whose history was erased. The
conservative reading is to treat the erased history as unknown exposure
— censored, like an in-flight conversion in delayed feedback — rather
than as zero, which is what the cap currently assumes.

## Who owns the loop

The cap only works if someone owns each side of the identity loop:

- **The delivery and ads-serving team** owns the cap's execution: the
  counter read at serve time, the identity lookup, and the fallback
  when the lookup fails. It owns the over-serve failure — the audit
  measured 6,167 extra impressions when the counter resets, served past
  the useful exposure range at 0.0139 clicks per impression.
- **The data and identity team** owns the identity graph that makes the
  counter stable: device graph, login bridge, and the join of serving
  logs to stable humans. It owns the resets — a cookie that clears is a
  counter that vanishes, and the cap inherits the identity's fragility
  (Buchbinder, Feldman, Ghosh & Naor, 2014, J. Scheduling, analyze
  frequency capping with identities and show the cap's guarantees
  depend on the identity the campaign is capped by; Aharon et al.,
  2023, arXiv:2312.05052, report a 7.3 percent revenue lift from soft
  frequency capping in Yahoo Gemini Native, which is the value a
  working cap protects).
- **The ads-measurement team** owns the counter-health monitor: served
  exposure per stable human, reset rate by identity type, and the dead
  share of delivered impressions. It owns the invisible-symptom failure
  — the 0.0355-versus-0.0400 click rate that hides 6,167 wasted
  impressions from a campaign-level report.

When the ownership is implicit, serving trusts the counter it reads,
identity ships no graph, and the reset rate rises quietly while
campaign CTR stays flat — the over-serve is paid for by the advertiser
and never counted by anyone.

## The fix and its trade

The measured fix is to reconcile the counter against a stable identity
before the cap decides. For logged-in traffic, key the counter to the
user id and merge device counters through the graph; for anonymous
traffic, treat a reset counter as censored exposure — serve on the
probability the true exposure is still below the cap, the same
survival-style estimate delayed feedback uses for labels. The trade is
on the reconciliation: merging aggressively (device graph over-joins)
under-serves reach by capping two different humans as one, while
merging timidly over-serves the fatigue the cap exists to stop. Aharon
et al. (2023) show the reward side of getting it right — soft capping
lifted revenue 7.3 percent in a bucket test — and Buchbinder et al.
(2014) show the constraint side: the cap is only as strong as the
identity it is keyed to. The executed table is the cost of skipping
the fix: 6,167 impressions at a third of the click value.

## Evidence boundary

The executed audit uses a declared reset-rate model over 10,000
synthetic users (fixed seed) with the stage's decay curve. It
demonstrates the over-serve mechanism; real identity failure rates are
measured per browser, app, and market, and real reconciliation
evaluates the merge's false-positive cost against the over-serve it
removes.

## Check your mental model

Answer each before opening it.

**1. Why does the cap restart when a cookie clears?**

<details>
<summary>Answer</summary>

Because the counter is keyed to the cookie, not to the human. The
platform enforces "three exposures per identity," and a cleared cookie
is a new identity with a counter of zero — so the cap starts over and
the same human receives the full cap again. The audit served 6,167
extra impressions this way: 30 percent of users reset at least once,
and each reset re-opened the cap.

</details>

**2. How do you find the over-serve in production?**

<details>
<summary>Answer</summary>

Not from campaign CTR — the audit's clicks per impression fall only
from 0.0400 to 0.0355. Measure served exposure per stable human: join
the serving log to a logged-in id or device graph, count delivered
impressions past the cap, and watch the reset rate by identity type.
The dead share column — impressions at or below 0.005 CTR — is the
operational alarm; it rose from 0.0 to 3.1 percent in the audit.

</details>

## Next

Back to [stage 25](../), where the cap is a value decision. The
[cap-bites detour](../when-the-cap-bites/) shows the cap's other cost —
shrinking reach — and the [fatigue detour](../when-fatigue-hits/)
prices what the cap saves.
