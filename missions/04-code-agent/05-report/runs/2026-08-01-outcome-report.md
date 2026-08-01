# Mission 04 outcome report, mechanically checked against its own contract

`report.py` reads stage 00's task manifests and stage 01/03's `runs/` JSONL
directly and holds every real number against `mission.yaml`'s seven
`acceptance` bullets, verbatim. It does not get to pick a more flattering
comparison after seeing the numbers, and a bullet this mission's stages never
built the data for is printed `CANNOT DETERMINE`, not skipped.

## Command

```bash
cd missions/04-code-agent/05-report/core
uv run python report.py
```

Full output: [`2026-08-01-outcome-report.txt`](2026-08-01-outcome-report.txt).

## Verdict, bullet by bullet

1. **Beats no-harness on resolve rate beyond spread, both task sets --
   PARTIAL.** Per-tier on the private set, the harness beats no-harness
   decisively at `haiku` (margin +1.000 against 0 spread) and `sonnet` (+0.833
   against 0.5 spread); at `opus` the margin (+0.500) is smaller than the
   no-harness arm's own run-to-run spread (1.000) over 2 tasks x 3 runs, so
   that tier is a genuine no-result, not a loss. The public set now exists
   ([stage 00's second run](../../00-task-set/runs/2026-08-01-public-task-set.md),
   2 tasks mined from more-itertools) and has a real harness result --
   haiku, 6/6 resolved across 3 repeats -- but no no-harness control has been
   run against it. The bullet's comparison cannot complete for the public half
   without that control, so it stays short of MET, but it is no longer
   CANNOT DETERMINE for the reason it was before (a set that did not exist).
2. **Beats always-frontier on $/resolved without losing resolve rate -- MET.**
   `haiku` ($0.1604/resolved) beats `opus` ($0.8226/resolved) with identical
   6/6 resolve rate. Scope note carried forward honestly: the three tiers
   stage 03 ran are three hosted-subscription tiers of one CLI, not an actual
   local-lane open-weights model against a hosted frontier one, as
   `mission.yaml`'s `decision` field names. That gap predates this report and
   was not something stages 01/04/05 were asked to close.
3. **Guardrail regression + tampering-fired-or-honestly-not -- MET.** Zero
   regressions across all 42 real attempts (36 private + 6 public). Zero real
   tampering firings; reported as "never fired," with stage 02's scripted
   demonstration cited but not counted as a real firing.
4. **Public/private reported separately, never pooled -- MET.** The public
   task set now exists and has a real result: private (stage 03 harness, all
   tiers) 18/18 resolved; public (haiku only) 6/6 resolved. Reported side by
   side above, never averaged into one figure.
5. **Latency and dollars measured on real runs, inside budget -- MET.** p50/p95
   wall-clock reported per arm from real records; $14.9034 real spend across
   42 attempts against the $30 ceiling this stage declared (the public run
   added $0.6407 on top of the $14.2627 already spent by stages 01+03).
6. **Failures catalogued by category -- MET.** See
   [stage 04](../../04-how-it-fails/).
7. **Every number traceable to a runs/ entry -- MET.** This script reads only
   from committed JSONL; nothing above was hand-typed.

**Overall: 6 of 7 MET, 1 of 7 PARTIAL** -- stage 00's public task set was built
after this report first ran (2 tasks mined from more-itertools, MIT-licensed,
same fail-at-base/pass-at-gold admission rule as the private set) and a real
haiku harness run against it resolved 6/6. Bullet 4 is now fully answerable and
MET. Bullet 1 needs a no-harness control on the public set to fully resolve,
which this update did not build (out of the scope that added the public set
itself) -- it is reported PARTIAL rather than forced to MET or NOT MET.

## What this does not establish

**A PARTIAL is not a NOT MET.** Bullet 1's public half is missing one input --
a no-harness attempt against the public set -- not evidence the harness would
lose there. If that control is ever run, this same script resolves the bullet
fully without modification.

**The opus-tier no-result in bullet 1's private half is a small-N property,
not a claim that the harness stops mattering at the frontier tier.** Two tasks
and three runs is the entire private task set this mission has; a larger one
could resolve the question either way.

**haiku 6/6 on the public set says nothing about resolve rate on public bugs
in general.** N=2, one model tier, one repository this model may have seen in
training. Per [the public-set run's own boundary](../../00-task-set/runs/2026-08-01-public-task-set.md),
"public and plausibly memorized" describes the repository's visibility, not a
verified fact about haiku's training data.
