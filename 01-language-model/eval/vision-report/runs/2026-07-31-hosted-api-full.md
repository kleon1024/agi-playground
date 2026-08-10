# Hosted VLM API: full 784-question eval set

## Command

```bash
export OPENROUTER_API_KEY=...
cd 01-language-model/vision/02-report/core
uv run python call_hosted_api.py --resume
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 (network-bound, not compute-bound) |
| Model | `openai/gpt-4o-mini` via OpenRouter (`https://openrouter.ai/api/v1/chat/completions`) |
| Repository HEAD | `93489a4` |
| Real dollar cost | \$1.0033 total, \$0.00128/question (from OpenRouter's `usage.cost`, not estimated from token counts) |

Preceded by an 8-call pilot (see
[`2026-07-31-hosted-api-pilot.md`](2026-07-31-hosted-api-pilot.md)) that
confirmed the request/response contract and projected this cost and
duration before the full run started.

## What ran

All 784 QA pairs from stage 00's held-out eval set -- the same set stage 01
scored the vision and text-only pathways on. Each question's image (raw
32x32 RGB pixels from `00-image-caption-task/data/raw/eval.jsonl`) is encoded
as a real PNG with `core/png_encode.py` (a from-scratch, stdlib-only encoder;
no hosted vision API accepts stage 00's raw pixel array or PPM format), sent
as a base64 data URL alongside the question text and the instruction "answer
with a single word or number only, no punctuation." Results are appended to
`hosted-api-raw.jsonl` as they arrive, one line per question, so a network
failure partway through a paid run does not throw away money already spent.

## Result

```
overall exact-match: 0.8329  (653/784)
total cost: $1.0033
wall-clock: 1343s (22.4 min), sequential HTTP calls, avg 1.7s/call
```

By question category:

```
shape_color    253/261 (96.9%)
presence        76/83  (91.6%)
column_shape   194/239 (81.2%)
shape_count     77/101 (76.2%)
total_count     53/100 (53.0%)
```

The hosted model is decisively better than either self-trained pathway on
every category, and worst (though still clearly above chance) on
`total_count` -- the same category stage 01's category breakdown identifies
as the specific failure point for the self-trained models too (see
[`2026-07-31-category-breakdown.md`](2026-07-31-category-breakdown.md)).
Counting shapes in a small pixelated image is evidently the hardest
sub-task for all three pathways, hosted included, not a weakness specific to
this mission's own architecture.

## What this run does not establish

Only one model (`openai/gpt-4o-mini`) and one prompt phrasing were tried; a
different hosted model or a few-shot prompt could plausibly score
differently. No claim about hosted-API quality on real photographs -- the
image set is the same synthetic, disjoint-checked set every other stage in
this mission uses. The full outcome verdict, combining this baseline with
stage 01's vision/text-only numbers against mission 05's own acceptance bar,
is in [`../README.md`](../README.md) and produced by `core/report.py`.
