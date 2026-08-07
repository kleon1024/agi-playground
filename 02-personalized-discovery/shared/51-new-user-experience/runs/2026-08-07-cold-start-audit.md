# Run — the onboarding-path cohort audit over the emitted path rows

**Commands:** `uv run python core/cold_start.py --emit-log /tmp/cold-start-envelope.json`;
`uv run python prod/cold_start_audit.py /tmp/cold-start-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 51's read shows the first page improving as the trail builds. This
run is the case-finding half of the stage: new users arrive by different
onboarding paths, and the aggregate first-page number blends them, so a
path that actively loses users is invisible until you stratify by path.
The core script emits the per-path first-page rows; the production audit
compares each path against the popularity default and the no-ask
baseline, the way a growth team reads acquisition funnels.

## Output

```
new-user cohort audit (first page by onboarding path):
  path          traffic first-page ndcg  vs 0.122 retention vs no-ask
  popularity        60%           0.122    +0.000      0.24     +0.04
  right prior       20%           0.878    +0.756      0.55     +0.35
  wrong prior       10%           0.000    -0.122      0.18     -0.02
  no-ask            10%           0.050    -0.072      0.20     +0.00
  aggregate        100%           0.254    +0.132      0.29     +0.09

verdict: NEW-USER GAP -- the wrong prior path serves
0.000 first-page relevance, below
the 0.122 popularity default, and its retention
(0.18) is below the no-ask baseline
(0.20): a confident wrong prior is worse than asking nothing.
The aggregate (0.254) hides it because 60% of new users arrive
via popularity; stratify by path before declaring the first-
page policy healthy, and route the failing path back to the
default while the prior is re-measured.
```

## Notes

- The wrong-prior path serves 0.000 first-page relevance — below the
  0.122 popularity default — and earns 0.18 retention, below the 0.20
  no-ask baseline: a confident wrong prior is worse than asking nothing.
- The aggregate (0.254) hides the failure because 60% of new users
  arrive via popularity, which scores exactly at the baseline. The
  audit's message is the stage's: before declaring the first-page
  policy healthy, stratify by onboarding path, and route a failing path
  back to the default while its prior is re-measured. Cold-start
  surveys (Abdullah et al., Applied Sciences 2021) catalogue exactly
  this prior-quality problem across user-side, item-side, and
  system-side cold start.
