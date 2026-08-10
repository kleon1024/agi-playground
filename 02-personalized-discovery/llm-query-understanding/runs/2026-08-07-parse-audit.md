# Run — parse-stability audit, executed on the head/tail query log

**Date:** 2026-08-07
**Command:** `uv run python core/intent_slots.py --emit-log /tmp/parse-envelope.json` then `uv run python prod/parse_audit.py /tmp/parse-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; core script stdlib only, audit script pandas.
**Wall-clock:** 0.5s total.
**Cost:** \$0 (local lane).

## Purpose

Stage 37 parses a raw query into intent and slots with an LLM. This run
stratifies parse agreement and quality by head and tail on a 10-query
log and finds where the parse actually decides — the case-finding for
the LLM path.

## Output

```
parse-stability audit over the 10-query log:
  aggregate parse quality: 0.765  mean agreement: 0.760

  stratum  queries  agreement  quality  low-conf slots
  head     5        1.000    0.976  0.0
  tail     5        0.520    0.554  2.4

verdict: PARSE QUALITY HIDES SWINGING JUDGMENT CALLS -- the
aggregate quality 0.765 is a head
artifact: head parses agree at 1.000
and score 0.976, while tail parses agree
at only 0.520 — the same query parses into
different intents across samples, so a low-confidence call
flips the retrieval path. Sample the parse and take the
majority (self-consistency), and treat a low-confidence slot
as a clarification or a broadening, never a silent guess.
```

## Notes

- Aggregate parse quality of 0.765 is a head artifact: head parses agree
  at 1.000 and score 0.976, tail parses agree at only 0.520 with 0.554
  quality and 2.4 low-confidence slots per query.
- The decision that follows: sample the parse and take the majority
  (self-consistency; Wang et al., ICLR 2023, arXiv:2203.11171), and
  treat a low-confidence slot as a clarification or a broadening,
  never a silent guess.
