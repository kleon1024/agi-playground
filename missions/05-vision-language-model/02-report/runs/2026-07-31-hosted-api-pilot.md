# Hosted VLM API pilot: 8 real calls, before committing to the full run

## Why this exists

Before spending real money and 20 real minutes on the full 784-question eval
set, an 8-call pilot checked three things a repository's own "if you cannot
run it, do not write the number" rule requires knowing in advance, not
assuming: (1) does OpenRouter's API actually accept a from-scratch PNG
encoding of stage 00's raw pixel arrays, (2) what does a real per-call dollar
cost look like, so the full run's cost is a measurement, not a guess, and (3)
is the answer format usable for exact-match scoring at all.

## Command (ad hoc, not committed as a script — superseded by `call_hosted_api.py`)

Eight real calls to `openai/gpt-4o-mini` via `https://openrouter.ai/api/v1/chat/completions`,
one image (encoded with the PNG encoder now at `core/png_encode.py`) plus one
question per call, `usage: {include: true}` requested so the response
carries a real `usage.cost` field rather than a token count this report
would have to price itself.

## Result

```
8/8 exact-match correct
elapsed: 12.6s for 8 calls (avg 1.57s/call)
total real cost: $0.01024 (avg $0.00128/call)
projected for the full 784-row eval set: ~20.5 min, ~$1.00
```

Every one of the 8 pilot answers was a single clean word or number
(`circle`, `no`, `2`, `blue`, ...), confirming the "answer with a single
word or number only" instruction is followed closely enough for exact-match
scoring without a parsing layer.

## Decision

$1 and 20 minutes is well inside mission 05's own cost_budget for a synthetic,
small-by-design task, and using the full 784-row eval set rather than a
sub-sample means the hosted-API baseline is scored on literally the same set
stage 01's vision and text-only models were scored on — no sampling caveat
needed. The full run is `core/call_hosted_api.py`, recorded in
[`2026-07-31-hosted-api-full.md`](2026-07-31-hosted-api-full.md).
