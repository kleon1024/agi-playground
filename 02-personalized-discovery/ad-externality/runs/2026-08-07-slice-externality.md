# Run — the hidden-slice externality audit

**Date:** 2026-08-07
**Command:** `uv run python core/slice_externality.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.12s.
**Cost:** \$0 (local lane).

## Purpose

The stage run shows one slate's displacement. The audit asks the
case-finding question at production scale: whose organic value do the ads
actually displace? It draws 20,000 users (fixed seed) in two slices — a
casual slice whose organic items are low-value, an engaged slice whose
items are high-value — shows one ad per user (utility 0.40), and reports
per-slice and aggregate displacement and net value.

## Output

```
hidden-slice externality audit: 20,000 users, one ad per user,
ad utility 0.40; the ad displaces the bottom-ranked organic item

     slice   share  displaced  net/user
    casual   75.0%     0.2000    0.2000
   engaged   25.0%     0.7249   -0.3249
  aggregate    100%     0.3312    0.0688
```

## Notes

- The aggregate net is +0.0688 per user — slightly positive, so an
  ad-load decision made on the aggregate keeps the ad. The engaged slice
  is -0.3249: its organic items are worth ~0.72, and the ad displaces
  them for 0.40 of utility. The slice that pays is the high-value one
  the platform can least afford to damage.
- The dilution is arithmetic, the same pattern as the stage-16 slice
  audit: a 75 percent neutral-to-positive majority hides a 25 percent
  negative slice. Stratifying net ad value by user slice is how the
  case is found.
- Organic slate values drawn per user from the slice range with a fixed
  seed; ad utility assumed constant. Illustrative and deterministic,
  not measured organic-value loss.
