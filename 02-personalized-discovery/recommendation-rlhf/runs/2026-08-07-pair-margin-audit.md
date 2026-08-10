# Run — the margin-stratified pair audit over the preference log

**Date:** 2026-08-07
**Command:** `uv run python core/preference_opt.py --emit-log /tmp/pair-margin-envelope.json` then `uv run python prod/pair_margin_audit.py /tmp/pair-margin-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 32 trains a ranker from pairwise preferences. The failure mode
this audit exists for is the near-tie pair: when two items score almost
the same, label noise decides which one is reported as chosen, and the
model learns a wrong gradient from a preference that was never really
there. The audit stratifies a 20-pair log by margin and reports the
flip rate and the Bradley-Terry loss under clean and observed labels —
the case-finding that shows which pairs the annotator, not the user,
created.

## Output

```
margin-stratified pair audit over the 20-pair log:
  aggregate flip rate: 0.20

  stratum  pairs  mean margin  flips  flip rate  clean loss  observed loss
  head     10     1.140    0     0.00    0.280     0.280
  tail     10     0.039    4     0.40    0.674     0.689

verdict: NEAR-TIE PREFERENCES FLIP UNDER LABEL NOISE --
head pairs (mean margin 1.14) are
stable: 0/10 flips, observed loss equals clean
loss. Tail pairs (mean margin 0.039)
flip at 4/10 -- the reported
preference contradicts the true one and forces a wrong
gradient. The aggregate flip rate 0.20
hides that every flip is a near tie. Sample pairs by
margin, re-ask low-margin preferences, and evaluate on
high-margin held-out pairs; otherwise the tail preference
is the annotator, not the user (Rafailov et al. 2023,
Zhang et al. 2025).
```

## Notes

- The audit cohort is a 20-pair log with per-pair chosen and rejected
  scores and a flip flag for the observed label. Head pairs (mean
  margin 1.140) are stable: 0/10 flips, and the observed loss equals
  the clean loss at 0.280. Tail pairs (mean margin 0.039) flip at
  4/10, raising the observed loss from 0.674 to 0.689 and forcing a
  wrong gradient on each flipped pair.
- The aggregate flip rate of 0.20 is a tail artifact: every flip is a
  near tie, where the annotator's preference is a coin flip under
  noise. The preference signal in the tail is label noise, not user
  signal.
- Rafailov et al., "Direct Preference Optimization", NeurIPS 2023,
  arXiv:2305.18290, is the objective reference — the model optimizes
  the same Bradley-Terry log loss this audit measures. Zhang et al.,
  "Beyond Bradley-Terry Models: A Review and Open Problems", ICML
  2025, arXiv:2410.02197, is the limitation reference — scalar
  preference models break down exactly where the near-tie pairs live,
  which the when-the-preference-cycles detour reads. The decision
  that follows: sample pairs by margin, re-ask low-margin
  preferences, and evaluate on high-margin held-out pairs.
