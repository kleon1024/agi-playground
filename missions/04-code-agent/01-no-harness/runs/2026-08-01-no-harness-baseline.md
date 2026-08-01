# The no-harness baseline: one blind call, no tools, no feedback, no retry

Eighteen attempts: two private-set tasks, three model tiers, three independent
runs each -- the same matrix stage 03 ran through the full agent harness. This
is the control stage 03's own README named and never ran: "the value of the
loop over a single call is still unmeasured." It is measured here.

## Command

```bash
cd missions/04-code-agent/01-no-harness/core
for m in haiku sonnet opus; do
  uv run python no_harness.py --model $m --repeats 3 \
      --out results.jsonl --keep-diffs ../runs/diffs \
      --ceiling 30 --already-spent <cumulative-so-far> --timeout 240
done
```

## What "no harness" means here, concretely

One `claude -p` call per attempt with every tool Claude Code has denied via
`--disallowedTools` (not an empty allow list -- an explicit deny list, for the
same reason `claude_arm.py` denies the web tools explicitly rather than
leaving them off an allow list). With no `Read` tool, the model cannot see the
repository unless the prompt puts it there, so the prompt includes the current
contents of exactly the source file(s) `mine_history`'s task construction
already names as the ones the gold patch touches -- what the SWE-bench
literature calls **oracle file location**. This baseline is not measuring "can
it find the bug," only "can it fix the bug once told where it is." Stage 02/03's
harness has to find that file itself via `Grep`/`Read`; this baseline is handed
that step for free and still only gets one blind attempt at the patch itself.

The model replies with a unified diff and nothing else (there is no `Edit` tool
to call). `no_harness.py` applies that diff with plain `git apply`, blind: no
retry, no repair, no second prompt if it fails to apply. A wall-clock cap of
240s per attempt is declared once and applied to every attempt in this run,
including the two that hit it -- per `mission.yaml`'s guardrail, a timeout is
scored as a failure, not retried with a longer cap.

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Agent | Claude Code, headless (`claude -p --output-format json`), zero tools allowed |
| Models | `haiku`, `sonnet`, `opus` as resolved by the CLI on 2026-08-01 |
| Wall-clock cap | 240s per attempt, declared once, applied to every attempt |
| Task isolation | one-commit repository per attempt, no route to the fix commit |
| Cost ceiling | $30 total mission hosted-API spend, declared before this stage's first run (mission.yaml names a ceiling qualitatively but stage 03 never printed a number; this is the first stage to fix one). Stage 03 had already spent $9.12; this stage spent $5.1438; cumulative $14.2638. |

## Resolve rate and cost

| Model | Task | Resolved | Patch applied at all | $/attempt (mean) |
|---|---|---|---|---|
| haiku | `354c352` | 0/3 | 0/3 | 0.0749 |
| haiku | `b81c414` | 0/3 | 1/3 | 0.0892 |
| sonnet | `354c352` | 0/3 | 0/3 | 0.2824 |
| sonnet | `b81c414` | 1/3 (2/3 timeout) | 1/3 | 0.1757 (mean over 3 attempts; 2 timed out at $0) |
| opus | `354c352` | 2/3 | 3/3 | 0.5340 |
| opus | `b81c414` | 1/3 | 1/3 | 0.5584 |

| Model | Resolve | Total cost | $/resolved |
|---|---|---|---|
| haiku | 0/6 | $0.4921 | n/a (0 resolved) |
| sonnet | 1/6 | $1.3744 | $1.3744 |
| opus | 3/6 | $3.2773 | $1.0924 |

Total for this stage: **$5.1438** over 18 attempts (cumulative mission spend
$14.2638, against the $30 ceiling).

Raw records: [`no-harness-results.jsonl`](no-harness-results.jsonl). Diffs
(where a patch was produced) are kept alongside these records in `diffs/`, one
per attempt.

## Compared against the harness (stage 03), per tier

`mission.yaml`'s discipline: a margin only counts if it exceeds the run-to-run
spread (`max - min` of each independent run's resolved fraction, the same
convention `platform/training/02-architecture-ablations` and mission 06's
report use for a continuous metric, applied here to a binary per-attempt
outcome since that is what this mission's primary metric actually is).

| Tier | Harness (stage 03) | No-harness (this stage) | Margin | Spread | Decisive? |
|---|---|---|---|---|---|
| haiku | 6/6 (per-run [1,1,1], spread 0) | 0/6 (per-run [0,0,0], spread 0) | +1.000 | 0.000 | **yes** |
| sonnet | 6/6 (per-run [1,1,1], spread 0) | 1/6 (per-run [0.5,0,0], spread 0.5) | +0.833 | 0.500 | **yes** |
| opus | 6/6 (per-run [1,1,1], spread 0) | 3/6 (per-run [0,0.5,1], spread 1.0) | +0.500 | 1.000 | **no -- inside spread** |

Pooled across tiers: harness 18/18, no-harness 4/18. At haiku and sonnet the
gap is decisive by a wide margin -- the loop is doing real work, not just
adding cost. At opus specifically, the no-harness arm's own run-to-run spread
(0 -> 0.5 -> 1.0 resolved fraction across its three repeats) is as large as
the margin itself. With only 2 tasks and 3 repeats, that is not evidence the
loop stops mattering at the frontier tier; it is evidence this task set is too
small to say either way at that tier. Reported as no result, not rounded into
a win.

## Why the model that resolved fewer tasks still cost more per success

Cost per resolved task is *higher* for every no-harness tier than the matching
harness tier (haiku n/a vs $0.1604; sonnet $1.3744 vs $0.5369; opus $1.0924 vs
$0.8226) -- despite each individual no-harness call costing less than a full
tool-loop attempt. The reason is the denominator: a $0 timeout and five wrong
patches still cost real dollars, and dividing by a much smaller resolved count
punishes cost-per-resolved harder than it helps cost-per-attempt. This is
exactly the distinction `mission.yaml` names cost-per-attempt as the wrong
number for: it flatters whichever arm fails cheapest, and the no-harness arm
fails often and not particularly cheaply.

## How it failed: a preview of stage 04

Twelve of eighteen attempts landed on `target_still_failing`, and of those,
eleven produced a diff `git apply` rejected outright -- not a patch that was
wrong, a patch that was not well-formed enough to apply at all. One inspected
by hand (`haiku`, `354c352`, run 2) had a hunk header claiming 17 old-side
lines and 43 new-side lines against content that was actually 19 and 42 lines
-- the model miscounted its own diff. Two attempts (both `sonnet` on
`b81c414`) hit the declared 240s cap and produced nothing at all. Full
breakdown, including a comparison against stage 03's zero real failures, is
[stage 04](../../04-how-it-fails/).

## What this does not establish

**N = 2 tasks.** Every number above inherits stage 00's own limitation: two
tasks support no significance claim, and the `opus`-tier "no result" finding
above is the sharpest illustration of that limit inside this very stage.

**Only the private set.** Stage 00 never built a public task-set companion, so
this baseline -- like stage 03 before it -- ran only against the private set.
`mission.yaml`'s acceptance bullet asking for "both task sets, never pooled"
cannot be evaluated here for the same reason stage 03 could not evaluate it:
there is nothing to pool the private set with. See [stage 05](../../05-report/)
for the mechanical acceptance check.

**Oracle file location, not oracle-free.** This baseline was told exactly
which file(s) needed a fix. A bug report that only comes with an issue and a
failing test -- no file pointer -- is a strictly harder problem than the one
measured here, in either arm.

**No retry ever happened, on purpose.** A timeout or a malformed diff was
never given a second attempt. That is the point of a no-harness control, not
a limitation of this run.
