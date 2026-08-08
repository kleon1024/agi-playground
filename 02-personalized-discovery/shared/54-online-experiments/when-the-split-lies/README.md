---
status: verified
level: applied
base: scratch
label: When the split lies
verified: 2026-08-07
---

# The split check fires before the outcome test has power

**Question:** [stage 54's gate](../) treats the allocation-ratio check as
one validity condition. This chapter drills into the most common way the
split lies — the bucketing hash drifts from the declared ratio — and
measures how early the check fires compared with the outcome test.

**Before this:** [stage 54's gate](../) for the SRM check and its place in
the verdict, and [stage 43 — feature store](../../43-feature-store/) for
the sibling discipline of training/serving consistency.

## The bug, executed

The run ([record](runs/2026-08-07-srm.md)) simulates a one-constant edit:
the bucket threshold moved from 50 to 52 while the experiment config still
declares 50/50. Users hash deterministically (crc32), so the same user
always lands in the same bucket — the property a production bucketer must
have, since Python's salted built-in hash would change buckets across
processes.

| users | observed treatment | chi2 | p | check |
|---|---:|---:|---:|---|
| 500 | 52.60% | 1.35 | 0.245 | silent |
| 1,000 | 52.70% | 2.92 | 0.088 | silent |
| 2,000 | 52.75% | 6.05 | 0.014 | **FIRES** |
| 8,000 | 51.96% | 12.32 | 0.0004 | FIRES |
| 16,000 | 51.75% | 19.60 | 9.6e-06 | FIRES |

## Two findings

**The observed share is visibly wrong and the check still stays silent
for a while.** At 500 users the split is already 52.6% treatment, yet the
chi-square p-value is 0.245 — an eyeball on the ratio is not a test. The
check needs roughly 2,000 users to cross the 5% bar. SRM detection is
statistical, which is exactly why it is a daily automated check, not a
dashboard glance (Fabijan et al., 2019, KDD: diagnose sample ratio
mismatch before reading any outcome; Kohavi, Tang and Xu, 2020: SRM is the
most important experiment metric because it invalidates the experiment).

**The split check beats the outcome test by ~39x on the same traffic.** A
2% lift at 80% power needs 39,244 users per arm — 78,489 total — while the
split check fired at 2,000. The lesson for the interview and the team: you
do not wait for the outcome to discover the split is broken. The platform
owns the bucketing config, the experiment config owns the declared ratio,
and a daily allocation check enforces the match; the analyst owns reading
the result, not auditing the traffic plumbing after the fact.

## The fix and its trade

Correct the constant and the same users, same sessions, pass: the observed
split returns to 49.90% treatment with p=0.858. The trade is
organizational, not statistical: the fix is a one-line revert, but the
experiment already ran on the wrong split, and if it "won" while broken,
it has to rerun. The durable fix is the daily check plus a config that
declares the expected ratio at experiment creation, so a bucketing change
and a config change cannot drift apart silently. Cost: a small amount of
platform engineering, traded against every experiment that would otherwise
report a ghost.

## Who owns the loop

- **The experimentation-platform team** owns the daily allocation-ratio
  check and the config that declares the expected split at experiment
  creation, so bucketing and config cannot drift apart silently.
- **The bucketing and config team** owns the constant whose change broke
  the split, and the revert that restores it.
- **The product and analysis team** owns the rerun decision when an
  experiment "won" while the split was broken, since a ghost win is not
  a result.

## Evidence boundary

The simulation is deterministic (crc32 hashing, fixed user ids) and
illustrative: it demonstrates the detection mechanism and its traffic
requirements, not a real experiment's split. Real SRM causes — bucketing on
the wrong key, eligibility after bucketing, bots filtered unevenly — all
show up as the same observable: the allocation ratio deviates from the
declared split, and the chi-square test fires once traffic is large
enough.

## Check your mental model

**1. Why does the same 52% split take 2,000 users to detect?**

<details>
<summary>Answer</summary>

Because a 2-percentage-point deviation is within sampling noise until the
sample is large enough: chi-square grows with traffic, and the p-value
crosses 0.05 only around 2,000 users. The ratio is 52% at 500 users too;
the test is what separates signal from noise.

</details>

**2. Whose job is the daily SRM check?**

<details>
<summary>Answer</summary>

The experimentation platform's. It owns the bucketing hash, the experiment
config declares the expected ratio, and the check runs daily on every live
experiment. The analyst owns the outcome; the platform owns the traffic
plumbing. When the split lies, the analyst should find out from the
platform's alert, not from a suspicious dashboard.

</details>
