---
status: verified
level: applied
base: none
label: What the task set contains
verified: 2026-08-06
---

# What does the mined task set actually contain?

**Question:** [stage 00](../) mines bug-fixing tasks from repository
history, and its recorded runs report that only 2 of 6 public candidates
survive the admission rule. A task set is defined by what it excludes — this
chapter reads the funnel and the model's performance on what survived.

**Before this:** [stage 00's task mining](../) and its two recorded sets.

## The funnel, measured

The analysis ([record](runs/2026-08-06-task-set.md)) reads the recorded
public model-run log beside the recorded mining counts:

| stage | count |
|---|---:|
| more-itertools history | 2,423 commits |
| candidates admitted | 6 |
| survivors (fail-at-base / pass-at-gold) | 2 |
| model resolves (3 blind haiku calls each) | 6/6 |

**The admission rule is the bottleneck, not the mining.** 2,423 commits
shrink to 2 tasks — 0.08% of history. The rule (the bug's test must fail at
the base commit and pass at the fix) is a filter so strict that the mining
step barely matters by comparison; a task set is defined by the quality
bar, and this is the bar measured.

**What survived is resolvable — which is the point of the public set.** The
2 survivors resolve 6/6 across three blind calls each at \$0.107 mean. The
public set is the contamination-*prone* control: more-itertools is
plausibly inside the model's training data, so a high resolve rate is
expected and is not a capability claim. It exists to be the counterpart to
the private set — the same admission rule on a repository the model may
have seen — so the private set's numbers have something honest to be
compared against.

## The fix and its trade

The fix is the admission rule as the quality bar: 2,423 commits shrink to
2 tasks — 0.08% of history — because only a test that fails at base and
passes at gold is a real regression. The trade is that a task set is
defined by its exclusions: the rule removes 99.9% of candidates before a
model ever sees one, and the survivors are a tiny, selected sample, not a
distribution. The rule's strictness is what makes the resolved/failed
verdict meaningful, and the price is that the set can never claim to
represent "bug-fixing in general" — it represents the bugs that came with
tests and reproduced.

## Who owns the loop

- **The benchmark owner** owns the rule and the provenance: the public
  set is contamination-prone by design, and that label is a property of
  the owner's choice of repository, not of the model.
- **The evaluation owner** owns the interpretation discipline: 6/6 on a
  set the model may have seen is expected, not informative, and is
  reported as the counterpart to the private set's numbers.
- **The model owner** owns the non-claim: nothing here is a capability
  result, and a report that reads the public 6/6 as one has misread the
  control.

## Evidence boundary

Two recorded task sets, one 6-row model log; the mining counts are the
recorded run's. It shows the funnel's shape and the public set's
resolvability; it does not claim the resolve rate transfers to the private
set, and it does not measure how contamination changes the rate — the
comparison across sets is the mission's job.

## Check your mental model

Answer each before opening it.

**1. Why is the task set defined by its exclusions rather than its
inclusions?**

<details>
<summary>Answer</summary>

Because the admission rule removes 99.9% of the candidates before a model
ever sees a task. The fail-at-base/pass-at-gold filter is the real content:
it guarantees each task is a genuine regression — a test that was broken and
then fixed — which is what makes the resolved/failed verdict meaningful.
The mining finds candidates; the rule decides what a task is.

</details>

**2. The public set resolves 6/6. Why is that not evidence the models are
good?**

<details>
<summary>Answer</summary>

Because the public repository is chosen to be plausibly inside the model's
training data — contamination-prone by design. A high resolve rate on data
the model may have memorized is expected, not informative, which is exactly
why the set exists: it is the control that makes the private set's numbers
interpretable, not a benchmark of capability.

</details>

## Next

Back to [stage 00's task set](../), or forward to
[stage 01's no-harness baseline](../../01-no-harness/) where a single blind
call is measured against these tasks.
