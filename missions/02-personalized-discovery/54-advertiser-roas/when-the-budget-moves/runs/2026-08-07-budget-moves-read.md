# Run — when the budget moves, executed on the reallocation read

**Date:** 2026-08-07
**Command:** `uv run python core/budget_moves.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 54's detour: the advertiser spends across two channels and moves
budget toward the higher ROAS. This run reads platform revenue as the
share falls.

## Output

```
budget moves, read (advertiser splits $2000 by measured roas):
  platform share 100%: platform revenue $2000
  platform share 75%: platform revenue $1500
  platform share 50%: platform revenue $1000
  platform share 25%: platform revenue $500

reading: the platform's revenue is the advertiser's spend,
and the advertiser allocates by measured ROAS. When the
rival channel returns 4.6x and the platform 3.1x, the share
moves and platform revenue falls by half. The auction prices
a slot; it cannot price the advertiser's overall return -
that is a product decision about relevance and placement.
```

## Notes

- Platform revenue falls by half when the advertiser's share drops to 50% (\$2,000 to \$1,000).
- The auction prices a slot; it cannot price the advertiser's overall return — that is a product decision about relevance and placement.
