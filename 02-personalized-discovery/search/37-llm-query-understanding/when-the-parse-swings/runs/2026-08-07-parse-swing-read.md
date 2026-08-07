# Run — parse swing, executed on the five-sample parse read

**Date:** 2026-08-07
**Command:** `uv run python core/parse_swing.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 37 parses a raw query with an LLM. This run samples the parse
five times per query and reads how the intent swings.

## Output

```
parse swing, read (5 samples per query):
  'apple watch'
    product_search
    product_search
    service_search
    product_search
    service_search
  majority: product_search (3/5)
  'check my balance'
    bank_balance
    game_balance
    account_summary
    bank_balance
    game_balance
  majority: bank_balance (2/5)

reading: temperature sampling makes the parse a distribution,
not a point. 'apple watch' splits 3-2 between product and
service, and the minority parse routes to a different retrieval
path. 'check my balance' has no 3/5 majority at all. Sampling
plus majority (self-consistency) stabilizes the clear cases; a
thin majority means the query is a judgment call and should
broaden or clarify, not commit.
```

## Notes

- "apple watch" splits 3-2 between product and service; "check my
  balance" spreads 2-2-1 across three intents with no majority.
- The fix is sampling plus majority (self-consistency; Wang et al.,
  ICLR 2023, arXiv:2203.11171); a thin majority means broaden or
  clarify, not commit.
