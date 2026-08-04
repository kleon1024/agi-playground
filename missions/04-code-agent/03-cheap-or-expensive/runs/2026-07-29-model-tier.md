# Three model tiers against the private task set, and a probe on the patches

Eighteen attempts: two tasks, three model tiers, three independent runs each.
Every attempt resolved. The resolve rate therefore separates nothing, and the
useful part of this record is what happened when the patches were read instead
of counted.

## Commands

```bash
cd missions/04-code-agent/02-agent-loop/core
for m in haiku sonnet opus; do
  uv run python claude_arm.py --model $m --repeats 3 \
      --out results.jsonl --keep-diffs diffs
done

cd ../../03-cheap-or-expensive/core
uv run --group torch python probe_generality.py <path>/05-serve/core/engine.py
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 15.6.1, arm64 |
| Agent | Claude Code 2.1.220, headless (`claude -p --output-format json`) |
| Models | `haiku`, `sonnet`, `opus` as resolved by the CLI on 2026-07-29 |
| Tools allowed | Read, Glob, Grep, Bash, Edit, Write |
| Tools denied | WebSearch, WebFetch |
| Task isolation | one-commit repository per attempt, no route to the fix commit |
| Probe | torch 2.9.1 (CPU), `--group torch` |

Cost is reported by the CLI per invocation. This ran on a subscription, so
`total_cost_usd` is the **list-price equivalent** rather than money charged.
It is measured, not estimated, and it is per attempt.

## Resolve rate and cost

| Model | Task | Resolved | \$/attempt | Turns | Median wall-clock |
|---|---|---|---|---|---|
| haiku | `354c352` | 3/3 | 0.1239 | 7.7 | 63.9 s |
| haiku | `b81c414` | 3/3 | 0.1969 | 13.3 | 119.6 s |
| sonnet | `354c352` | 3/3 | 0.3885 | 7.0 | 41.4 s |
| sonnet | `b81c414` | 3/3 | 0.6852 | 12.7 | 98.2 s |
| opus | `354c352` | 3/3 | 0.7163 | 9.7 | 75.0 s |
| opus | `b81c414` | 3/3 | 0.9288 | 12.7 | 84.9 s |

| Model | Resolve | Total | \$/resolved |
|---|---|---|---|
| haiku | 6/6 | $0.96 | **$0.1604** |
| sonnet | 6/6 | $3.22 | $0.5369 |
| opus | 6/6 | $4.94 | $0.8226 |

Total for the matrix: **\$9.12**. No attempt was scored `tampered`,
`regressed`, or `no_tests_ran`; the guardrail did not fire on any real model.

Raw records: [`2026-07-29-results.jsonl`](2026-07-29-results.jsonl).

## The patches are not the same patch

All nine `b81c414` patches are in
[`2026-07-29-patches-b81c414.diff`](2026-07-29-patches-b81c414.diff). Three
strategies appear, split cleanly by tier:

- **opus**, 3/3 — imports `torch.nn.attention.bias.causal_lower_right`, the
  same construct as the original fix.
- **sonnet**, 3/3 — writes its own `causal_lower_right` boolean mask.
- **haiku**, 3/3 — disables masking during decode:
  `is_causal = (start_pos == 0)` in two runs, `is_causal = (T == k_full.size(2))`
  in the third.

Haiku's is correct when the query is a single token, because every cached key
is then in the past by construction and there is nothing to mask. It is wrong
as soon as a multi-token query meets a non-empty cache: nothing then prevents a
query from attending to a key later in its own block.

The target test runs a prefill and then single-token decode steps. It never
produces that shape.

## The probe

`core/probe_generality.py` runs a 4-token query against a cache holding 6, and
compares against a full recompute at the same tolerance the target test uses
(2e-5). It also checks the single-token shape, so a failure cannot be confused
with a patch that is simply broken.

| Patch | Single-token decode | 4-token query on a live cache |
|---|---|---|
| the original fix (control) | 5.960e-08 ok | 5.960e-08 ok |
| haiku run 1 | 5.960e-08 ok | **1.167e-03 wrong** |
| haiku run 2 | 5.960e-08 ok | **4.197e-02 wrong** |
| haiku run 3 | 5.960e-08 ok | **1.167e-03 wrong** |
| sonnet runs 1-3 | 5.960e-08 ok | 5.960e-08 ok |
| opus runs 1-3 | 5.960e-08 ok | 5.960e-08 ok |

**Haiku 0/3 general, sonnet 3/3, opus 3/3**, against a resolve rate of 18/18.

It is also the original bug displaced by one shape. `is_causal=True` was right
for prefill and wrong for decode. Haiku's fix is right for decode and wrong for
a multi-token query. A test written from one observed failure taught a fix to
cover that failure, and nothing in the loop asked for more.

## What this does not establish

**Haiku's patch is not wrong for this repository today.** `generate` only ever
issues a prefill followed by single tokens, so every call site in the tree is
within the range where the patch holds. It becomes wrong when someone adds
chunked prefill, speculative decoding, or prefix-cache reuse. That is a latent
defect, not a live one, and calling it a live bug would overstate the finding.

**One probe, one bug class, two tasks.** The probe was written after reading
the diffs, which is the correct order for discovering a failure mode and the
wrong order for estimating its frequency. Nothing here supports a rate at which
any tier produces over-narrow patches. A second probe on `354c352` was not
written; that task's fix has no comparable neighbouring shape.

**Tier names, not model versions.** `haiku`, `sonnet`, and `opus` are aliases
the CLI resolved on 2026-07-29. Re-running later may not run the same weights.

**Subscription pricing.** The dollar figures are list-price equivalents
reported by the CLI, not invoices. Ratios between tiers are the durable part;
the absolute numbers move with published pricing.

**Nothing about the harness.** These attempts ran through Claude Code's own
loop, not the from-scratch harness in
[stage 02](../../02-agent-loop/). The no-harness baseline in stage 01 has not
been run, so the value of a loop over a single call is still unmeasured.
