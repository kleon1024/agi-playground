# Run — the online value that moves between refreshes

**Date:** 2026-08-07
**Command:** `uv run python core/online_value_moves.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

The store freezes a value at ingestion; the refresh interval decides how
stale the served value gets before the world moves again. This run drops a
promo price mid-hour-2 and measures, for each refresh policy, how many of
the next 24 hours the served rank disagrees with the live truth.

## Output

```
online value moves, read (promo lands at hour 2, horizon 24h):
  live ranking after hour 2:
    1. P1001 (price $49, score 17.5)
    2. P1004 (price $39, score 15.5)
    3. P1002 (price $59, score 12.5)
    4. P1003 (price $19, score 11.5)

  refresh        stale hours  wrong pairs  pair-hours
  1h batch                 1            1            1
  4h batch                 2            1            2
  8h batch                 6            1            6
  24h batch               22            1           22
  streaming                0            0            0

reading: the store's guarantee is identical reads, not current
reads. With a 24h batch refresh the stale promo price ranks
P1002 below P1003 for 22 of 24 hours; streaming holds the
disagreement to zero - the change is served the hour it lands.
Freshness is a separate
decision per feature - the store keeps the two decisions from
colliding, it does not decide the latency class for you.
```

## Notes

- The change lands mid-hour-2, so any batch refresh serves the old price
  until its next re-ingestion: 1 hour for an hourly refresh, 22 hours for
  a daily one. The wrong pair is always P1002-versus-P1003, because the
  stale \$89 price scores P1002 below P1003 while the live \$59 price
  ranks it above.
- The trade is writes against freshness: hourly refresh re-ingests 24
  times a day, streaming per event, and the daily batch once. Real stores
  set the latency class per feature — Zipline serves from a 1-second
  realtime lane down to a daily batch lane, with sub-10ms online lookups
  (Simha and Hoh, Airbnb, Strata Data Conference New York, 2018).
