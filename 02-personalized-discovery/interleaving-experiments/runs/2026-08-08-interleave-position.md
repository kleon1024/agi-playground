# Run — interleave position bias, does the blend decide the winner

**Date:** 2026-08-08
**Command:** `uv run python core/interleave_position.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 38's executed credit model compares two rankings with one blended
list, and credits every click to the team that proposed the clicked
document. This run asks the industrial question that model skips: the
teams are equal, so any imbalance in the credited share comes from the
blend. It measures two blending policies against the same position
click probabilities and the same disjoint proposals: the naive policy
that lets team A start every session, and the balanced policy that
randomizes which team starts.

## Output

```
interleaving credit, audited: does the blend decide the winner?
  sessions: 10000 (fixed seed); position click probs:
    positions 1-6: 0.30 0.20 0.14 0.10 0.07 0.05
  team A proposes d1, d3, d5 | team B proposes d2, d4, d6

naive blend (team A starts every session):
  credited share: team A 59.2%, team B 40.8%
  sessions without a click: 14.0%
balanced blend (random start per session):
  credited share: team A 49.7%, team B 50.3%
  sessions without a click: 14.1%

reading: the teams are equal, so the difference is the blend.
The naive A-start list puts A at positions 1, 3, 5, whose
click probs sum to 0.51, and B at 2, 4, 6 (0.35). The audit
measures the result: A is credited 59.2% of
clicked sessions against 40.8% for B. Random
start averages the two lists and lands at 49.7%/50.3%. The fix is the random start, and the
trade is variance: each session flips, so the experiment needs
more sessions to see a real difference (Chapelle et al., 2012,
TOIS; Joachims et al., 2005, SIGIR; Radlinski & Craswell,
2010, SIGIR).
```

## Notes

- The teams are equal and the proposals are disjoint, so every credited
  difference is the blend's. The naive A-start list hands A positions
  1, 3, 5 (click probabilities summing to 0.51) and B positions 2, 4, 6
  (0.35), and the audit measures the result: A is credited 59.2 percent
  of clicked sessions against 40.8 percent for B.
- The balanced policy randomizes the start per session, averaging the
  two lists, and lands at 49.7/50.3 percent — the 59.2 percent was a
  position artifact, not a ranking win.
- The fix is the random start. The trade is variance: the start flips
  every session, so the experiment needs more sessions to resolve a
  real difference, which is the blend-bias detour's measured cost.
- Position-bias framing: Chapelle et al. (2012, TOIS); the position
  click model follows Joachims et al. (2005, SIGIR); interleaving's
  sensitivity advantage over between-user A/B is quantified by Radlinski
  & Craswell (2010, SIGIR).
