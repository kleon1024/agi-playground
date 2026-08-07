# Closing the loop: one retry turn with real outcome feedback

Real `claude -p` calls, no mocked model, no scripted backend. Twelve retry
attempts: every stage-01 no-harness attempt that did not resolve and was not a
timeout (six haiku, three sonnet, three opus -- the two sonnet/`b81c414`
timeouts produced no diff at all, so there was nothing to retry).

## Command

```bash
cd 04-agentic-platform/06-closing-the-loop/core
uv run python3 close_the_loop.py \
  --ceiling 30 --already-spent 15.0023 --timeout 240 \
  --out ../runs/closing-the-loop-results.jsonl \
  --keep-diffs ../runs/diffs
```

(`--already-spent 15.0023` already includes one smoke-tested attempt run
separately before the batch, at \$0.0989 -- `haiku`/`private-b81c414`/run1 --
recorded as the first line of `closing-the-loop-results.jsonl`.)

## Resolve rate: before (stage 01, by construction 0) vs after one retry

| Model | Retried | Resolved after retry | Diff even applied |
|---|---|---|---|
| haiku | 6 | 0/6 | 0/6 |
| sonnet | 3 | 1/3 | 1/3 |
| opus | 3 | 1/3 | 1/3 |
| **Pooled** | **12** | **2/12** | **2/12** |

Every attempt that resolved is exactly the attempt whose corrected diff
applied at all -- there is no case in this batch of a diff applying but
still leaving the target test failing. The retry step was fully bimodal:
either `git apply` rejected the corrected diff the same way it rejected the
first one, or the diff applied and the fix was correct. Ten of the twelve
retries produced a diff `git apply` still rejected, essentially reproducing
stage 04's "eleven of twelve never applied" finding at a slightly different
ratio (10/12 here) on a smaller, retry-specific sample.

## Cost

| Model | Cost this stage | Cumulative mission spend |
|---|---|---|
| haiku | \$0.4852 | -- |
| sonnet | \$1.3057 | -- |
| opus | \$1.2604 | -- |
| **Total this stage** | **$3.0513** | **$17.9547** |

Cost ceiling: \$30 total mission hosted-API spend (unchanged from stage 01's
declaration). Cumulative spend entering this stage was \$14.9034 (stage 03's
\$9.12 + stage 01's \$5.1438 + stage 00's public-set run's \$0.6407, per
`05-report`'s reconciled figure). This stage added \$3.0513, bringing the
cumulative total to \$17.9547 against the \$30 ceiling -- \$12.0453 of headroom
remained unused; the ceiling was never approached.

## Guardrails

Zero tampering (`tampered: []` on all twelve records), zero CLI errors, zero
timeouts. No regressions on either of the two resolved attempts.

## A note on an operational hazard, not a methods finding

Mid-batch, this stage's own output directory was briefly wiped by an
unrelated concurrent process sharing this working tree (visible collateral
evidence: untracked `platform/serving/03-speculative-decoding/` and modified
`site/*.generated.json` from a sibling task, neither authored by this stage).
The directory reappeared with all twelve records intact by the time this was
investigated, and the twelve real `claude -p` calls themselves were never
re-run -- the batch's own stdout transcript, captured independently by the
process that launched it, was cross-checked against the recovered JSONL
records field-for-field (model, task, verdict, cost, wall-clock) and the two
matched exactly. This is disclosed for the record, not because it changes
any number above.
