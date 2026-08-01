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
   CANNOT DETERMINE.** Per-tier, the harness beats no-harness decisively at
   `haiku` (margin +1.000 against 0 spread) and `sonnet` (+0.833 against 0.5
   spread); at `opus` the margin (+0.500) is smaller than the no-harness arm's
   own run-to-run spread (1.000) over 2 tasks x 3 runs, so that tier is a
   genuine no-result, not a loss. The bullet asks for both task sets, and only
   the private set was ever built by stage 00 -- there is no public set to
   report, so this bullet cannot be marked MET regardless of the private-set
   numbers.
2. **Beats always-frontier on $/resolved without losing resolve rate -- MET.**
   `haiku` ($0.1604/resolved) beats `opus` ($0.8226/resolved) with identical
   6/6 resolve rate. Scope note carried forward honestly: the three tiers
   stage 03 ran are three hosted-subscription tiers of one CLI, not an actual
   local-lane open-weights model against a hosted frontier one, as
   `mission.yaml`'s `decision` field names. That gap predates this report and
   was not something stages 01/04/05 were asked to close.
3. **Guardrail regression + tampering-fired-or-honestly-not -- MET.** Zero
   regressions across all 36 real attempts. Zero real tampering firings;
   reported as "never fired," with stage 02's scripted demonstration cited but
   not counted as a real firing.
4. **Public/private reported separately, never pooled -- CANNOT DETERMINE.**
   Same root cause as bullet 1: nothing has been pooled because there is
   nothing to pool the private set with.
5. **Latency and dollars measured on real runs, inside budget -- MET.** p50/p95
   wall-clock reported per arm from real records; $14.2627 real spend across
   36 attempts against the $30 ceiling this stage declared (stage 03 alone had
   no numeric ceiling on record before this).
6. **Failures catalogued by category -- MET.** See
   [stage 04](../../04-how-it-fails/).
7. **Every number traceable to a runs/ entry -- MET.** This script reads only
   from committed JSONL; nothing above was hand-typed.

**Overall: 5 of 7 MET, 2 of 7 CANNOT DETERMINE** -- both on the same root
cause: stage 00 never built a public task-set companion to the private one, so
neither "both task sets" bullet has data to evaluate. This is not a stages
01/04/05 defect; per this fork's mandate, stage 00 was read-only. It is the
most significant real gap this report surfaces, and it is reported here rather
than worked around.

## What this does not establish

**A CANNOT DETERMINE is not a NOT MET.** Bullets 1 and 4 are not failures of
the harness or the routing question; they are missing inputs stage 00 never
produced. If a public task-set companion is ever mined, this same script
re-evaluates both bullets against it without modification.

**The opus-tier no-result in bullet 1 is a small-N property, not a claim that
the harness stops mattering at the frontier tier.** Two tasks and three runs
is the entire task set this mission has; a larger one could resolve the
question either way.
