---
status: verified
level: applied
base: none
label: When breadth inflates the winner
verified: 2026-08-06
---

# When does a search over 1,000 signals find a loser that looks like a winner?

[Stage 01](../) measured its permutation null at the grid it actually
searched: 32 variants, best in-sample IC 0.0947, and 95 of 300 no-edge
searches matched or beat it. That number answers "is *this* winner
convincing?" and leaves a second question open: what would the same null look
like at the breadth a real research pipeline produces — a library of a few
hundred or thousand ideas? This chapter measures that curve.

**Before this:** [stage 01's search accounting](../), including its recorded
null and `search_log.jsonl`.

## The same null, at the breadth you actually search

The null is inherited verbatim from the stage's core: forward returns are
shuffled within each date, so no candidate can have a real relationship to
the return that follows it, and the best IC across the grid is recorded per
replicate. The only thing this chapter changes is the candidate generator —
pure-noise standard-normal exposures per name instead of the three signal
families — and the grid size, run at 32, 256, 1,024, and 4,096 candidates,
200 replicates each. The full record is in
[`runs/2026-08-06-best-of-n-null.md`](runs/2026-08-06-best-of-n-null.md).

| grid size N | best-of-N IC mean | median | max | P(best >= 0.0947) |
|---:|---:|---:|---:|---:|
| 32 | 0.0904 | 0.0891 | 0.1721 | 0.400 |
| 256 | 0.1240 | 0.1215 | 0.1834 | 0.960 |
| 1,024 | 0.1399 | 0.1378 | 0.1897 | 1.000 |
| 4,096 | 0.1572 | 0.1542 | 0.2088 | 1.000 |

Two readings fall out, and they are the point of the chapter.

**The winner's meaning is a function of the search, not of the signal.** The
recorded 0.0947 is beaten by pure noise 40% of the time at 32 candidates, 96%
of the time at 256, and in all 200 replicates at 1,024. At a thousand-idea
breadth, that number is the *expected* outcome of a noise search, not
evidence of an edge. This is selection bias made visible: the maximum of N
draws grows with N even when every draw is noise, and the growth here is
measured — mean best-of-N rises 0.090 -> 0.124 -> 0.140 -> 0.157.

**The calibration gap is itself informative.** The recorded null's best-of-32
mean was 0.0818; the synthetic best-of-32 here is 0.0904. The real variants
are structurally correlated with each other (momentum lookbacks, volatility
windows, value freshness), so their best-of-null is *lower* than i.i.d. noise
candidates produce. Read together: a grid of related variants is a smaller
search than its raw count suggests, and a library of independent ideas is a
larger one. Both are "the number of tries," but they are different tries —
the denominator has to know which.

## What the curve does for the next stage

Stage 03's walk-forward consumes `search_log.jsonl` and adjusts the later
evaluation for the search that produced the candidate. This chapter says the
adjustment cannot stop at the grid's line count: the same count carries
different selection pressure depending on whether the candidates were
independent or correlated. A search log that records candidate families and
their similarity gives stage 03 the information to make that distinction;
one that records only "32 tried" does not.

## Evidence boundary

This run measures a synthetic-noise null on a ten-name, continuously listed,
survivorship-limited universe — the same boundary stage 01 declares for its
own null. It demonstrates search accounting at scale, and it is not
investment evidence. It does not show that any real signal family inflates
identically to i.i.d. noise (the calibration gap says the opposite), and it
does not assign a defensible p-value to any real candidate — that is stage
03's job, armed with this curve's distinction between independent tries and
correlated variants.

## Reproducing

```bash
cd 03-quantitative-research/01-signal-research/when-breadth-inflates-the-winner
uv run python core/best_of_n_null.py --replicates 200
```

The script reuses stage 01's `signal_search` for fetch, forward returns, and
permutation; only the candidate generator and grid sizes are new.

## Check your mental model

Answer each before opening it.

**1. Why does the observed winner become ordinary at 1,024 candidates even
though the data did not change?**

<details>
<summary>Answer</summary>

Because the number itself was never an unconditional property of the signal —
it is the maximum of a search, and the maximum of N draws under a null grows
with N. The measured curve shows a 0.0947 best-of-grid is beaten by pure
noise in all 200 replicates at 1,024 candidates, so a researcher who searched
a thousand ideas and reports that winner is reporting the expected outcome of
their search procedure, not evidence of an edge.

</details>

**2. Why is the synthetic best-of-32 (0.0904) higher than the recorded
real-grid best-of-32 (0.0818), and what does the gap teach?**

<details>
<summary>Answer</summary>

Because the real 32 variants are structurally similar — momentum lookbacks,
volatility windows, value freshness — so their ICs are correlated and their
best-of-null is lower than what independent noise candidates produce. The gap
teaches that the search denominator is not just the count of candidates but
their independence: a grid of related variants is a smaller effective search
than its raw count, and a library of independent ideas is a larger one.

</details>

## Next

[Stage 03 — walk-forward validation](../../03-walk-forward-validation/): where
the search log gets consumed and the later evaluation is adjusted for the
search that produced the candidate.
