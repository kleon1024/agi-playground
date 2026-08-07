# Run — decode-recall audit, executed on the head/tail query log

**Date:** 2026-08-07
**Command:** `uv run python core/genret_read.py --emit-log /tmp/genret-envelope.json` then `uv run python prod/genret_audit.py /tmp/genret-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; core script stdlib only, audit script pandas.
**Wall-clock:** 0.5s total.
**Cost:** \$0 (local lane).

## Purpose

Stage 35 retrieves by decoding document IDs. This run stratifies decode
quality by head and tail on a 20-query log and finds where the generative
path holds — the case-finding that shows which queries it can actually
decode.

## Output

```
decode-recall audit over the 20-query log:
  aggregate recall@5: 0.770  emitted-ID precision: 0.870

  stratum  queries  recall@5  precision
  head     10       1.000    1.000
  tail     10       0.540    0.740

verdict: DECODE RECALL DIVERGES IN THE TAIL -- the
aggregate recall@5 0.770 is a head
artifact: head decodes perfectly (1.000) while tail
recall is 0.540 with precision 0.740 — a quarter of the emitted
IDs do not exist. The decode is a trained behavior, so it
inherits the training distribution. Gate the generative
path to queries it can decode, and fall back to the dense
or hybrid path for the tail.
```

## Notes

- Aggregate recall@5 of 0.770 is a head artifact: head decodes at 1.000,
  tail at 0.540 with 0.740 emitted-ID precision — a quarter of tail
  emitted IDs do not exist.
- The decision that follows: gate the generative path to queries it can
  decode and fall back to dense or hybrid for the tail. The tail of the
  query distribution is where the trained decode has the least evidence.
