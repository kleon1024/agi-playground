# Run — when the peak arrives, executed on the spike simulation

**Date:** 2026-08-07
**Command:** `uv run python core/peak_arrives.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.05s.
**Cost:** \$0 (local lane).

## Purpose

Stage 49's detour: traffic is provisioned for the average hour, and the
spike is several times it. This run simulates the base load at 1x, 2x,
and 5x and reads the queue's effect on latency.

## Output

```
peak arrives, read (base 30 req/s, service mean 17ms):
  1x peak (30 req/s): p50 10ms, p99 267ms, over 100ms 18.8%
  2x peak (60 req/s): p50 8737ms, p99 11850ms, over 100ms 99.4%
  5x peak (150 req/s): p50 108383ms, p99 208810ms, over 100ms 100.0%

reading: at 1x the service is comfortable; at 2x the tail
crosses the deadline; at 5x most queries miss it. The peak
does not raise the average - it floods the queue. Capacity
for the peak is bought with idle servers the rest of the
day, or paid for with dropped queries at the peak.
```

## Notes

- At 2x the p50 crosses into seconds (8737ms); at 5x 100% of queries miss the 100ms deadline.
- The peak does not raise the average — it floods the queue; capacity for it is bought with idle servers or paid for with dropped queries.
