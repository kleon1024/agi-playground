---
status: verified
level: applied
base: scratch
label: When the split leaks
verified: 2026-08-06
---

# The 99.1% leak: what the wrong split actually buys

**Question:** [stage 00](../) established that a time split leaks 0 of
1,223 test rows while a random split leaks 17,885 of 18,055 (99.1%) — the
model sees its own answer key. This chapter reads the recorded numbers and
asks what the leak actually changes in what you would report.

**Before this:** [stage 00's split](../), where the two splits are built and
the leak is measured.

## The comparison, read

The run ([record](runs/2026-08-06-split-leak.md)) reads the recorded
MovieLens split:

| split | test rows leaking the future | popularity hit-rate@20 |
|---|---:|---:|
| time | 0 / 1,223 | 0.0389 |
| random | 17,885 / 18,055 (99.1%) | 0.0496 |

One concrete leak: user 75's test row is timestamped 1,158,989,870, and that
same user's random-split train set holds a row 369 seconds later.

## Two readings

**The leak is not a small corruption; it is the baseline moving.** The
popularity floor itself shifts between the two splits — 0.0389 vs 0.0496
hit-rate@20. The floor is computed from the train set, so a leaking train
set does not merely flatter the model, it changes the number every later
stage is measured against. Comparing a model score on one split to a
baseline score on the other compares two different experiments, and the
leak is the reason nobody can tell.

**The leak's shape matters as much as its size.** 99.1% is not "almost
everything leaks, so the split barely matters" — it is the mechanism by
which a model memorizes a user's future: each user's later interactions sit
in the train set that predicts their earlier test rows. A time split
removes that mechanism by construction; no amount of model quality fixes a
mismatch that lives in the test, not in the model.

## Evidence boundary

The recorded MovieLens split run (2026-07-30), one dataset, one test
fraction. It reads the recorded numbers; it does not re-run the split and
does not extend the finding to other datasets or test fractions.

## Check your mental model

Answer each before opening it.

**1. The popularity floor is 0.0496 under the random split and 0.0389 under
the time split. Which one should you report?**

<details>
<summary>Answer</summary>

The time-split number (0.0389). The floor exists to answer "can this system
beat showing everyone the same popular items?" — and that question only
means something against the same boundary a live system operates under,
which never sees the future. The random-split floor is a number computed
from a leaking train set; reporting it would compare your model against a
baseline that was measured on different rules.

</details>

**2. Why does the 99.1% leak matter more than the 0.0107 floor shift?**

<details>
<summary>Answer</summary>

Because the floor shift is a symptom, not the problem. The leak means the
model itself is being trained on its own test answers — the popularity
floor moving is just the visible shadow of that. Fix the split and the
floor is whatever the honest boundary produces; keep the leak and every
downstream number is inflated by an unknown amount.

</details>

## Next

Back to [stage 00](../), or forward to
[stage 02 — recall](../../02-recall/) which is measured against the honest
split's floor.
