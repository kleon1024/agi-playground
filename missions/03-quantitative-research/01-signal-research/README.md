---
status: verified
level: applied
verified: 2026-07-27
---

# How many ideas may you try before the winner means nothing?

**Question:** you have the point-in-time panel from [stage 00](../00-market-data/)
and an idea. How many variants may you try before the winner is expected to look
good even when it has no edge?

The answer is not a permissible number. It is a recording requirement. A result
without its search denominator is not interpretable: one candidate that scores
well and the best of thirty-two candidates that scores well are different
claims. This stage produces candidate signals and a machine-readable search log;
[stage 03](../03-walk-forward-validation/) will consume that log when it adjusts
the later evaluation for the search that produced the candidate.

## Start from what was knowable

The panel is only honest if each input was public by the decision date. The
price at a rebalance date can be used then. Book equity cannot: the economic
period it describes may have ended long before the filing made it available.
The core harness therefore asks for the latest filing at or before each date,
not the latest database value for that fiscal period. This is an as-of join,
not a cosmetic data-cleaning choice.

Three candidates make that rule concrete. Momentum compares an older adjusted
price with a later one while optionally skipping recent months. Low volatility
uses only previous monthly returns. Book-to-market divides the most recently
filed equity by contemporaneous market equity, rejecting a stale filing. Each
has free parameters: lookback and skip windows, a volatility window, or allowed
ages for equity and shares. None may read a later price, filing, universe
membership, or full-sample normalization. A clean source panel does not save a
signal that recomputes its mean using future rows or selects the universe from
companies that exist today.

The ten-name example is deliberately not called survivorship-safe. It is a
hand-picked, continuously listed universe, so it cannot represent delisted
names. Stage 00 explains why free public endpoints cannot repair that boundary.
The harness demonstrates availability discipline and search accounting; it does
not claim a production-grade investment universe.

## Why the search count changes the claim

Three parameter grids here create 32 coded variants: 18 momentum combinations,
five volatility windows, and nine value freshness combinations. A grid is a
multiplication machine: two choices for one parameter and three for another
already create six hypotheses. Their tests may be correlated, but correlation
does not make selection harmless. Picking the largest noisy statistic introduces
selection bias; the selected value has been conditioned on being unusually high.

The recorded run makes that visible. The best real-data in-sample Spearman
information coefficient was 0.0947. On 300 within-date random permutations of
the forward returns, where ticker-to-return pairing has been destroyed but each
cross-section is preserved, the best-of-the-same-32-grid coefficient averaged
0.0818, had a median of 0.0794, and reached 0.2369. The observed winner was
matched or exceeded by 95 of 300 null searches (permutation p-value 0.317).
Those are not performance claims; they are the measured warning that this
selection procedure produces apparently promising winners under a null.

<!-- interactive: SearchLog -->

The widget uses the recorded null search as its default evidence boundary.
Changing the number of variants is a counterfactual resampling view, not another
market backtest. Its lesson is narrower and more important: an attractive maximum
cannot be read without knowing how many opportunities the process had to find
one.

## Make the log an artifact, not a memory

`runs/search_log.jsonl` has one JSON object per real candidate variant. Its
schema version, stage, family, parameters, universe size, date and observation
counts, in-sample statistic, data range, timestamp, and code path are written
by `evaluate_variant`'s harness path. A human does not transcribe the result
afterward; code that calculates a real-data statistic appends the same event.
The accompanying run record names the exact command and its output. These figures come from a trailing window fetched on the run date; re-running the command pulls a newer window and shifts them slightly, which the run record explains.

This is stronger than a paragraph saying “we tried a few.” Six months later,
another researcher can count the lines, inspect every parameter, and tell
whether the later multiple-testing adjustment used the right denominator. It is
also intentionally limited. The log sees variants that executed; it cannot see
ideas discarded before code existed, alternate notebooks, or unrecorded research
branches. A story about why momentum or value might exist is a weak prior that
can help decide what to test first. It is not evidence, because a story can be
attached to a winner after the fact.

## Run the mechanism

```bash
uv run python core/signal_search.py --range 5y --permutations 300
```

The standard-library core fetches Yahoo price events and SEC filings through
stage 00's code, builds signals date by date, records 32 variants, then shuffles
forward-return identities within each date to form the null. It is CPU-only.
The fixed permutation seed exists solely for reproducibility; it was not chosen
to make the output look interesting. See the recorded [run](runs/2026-07-27-core-signal-search.md).

`prod/pandas_search.py` expresses the same signal-and-log contract with pandas
and NumPy vector operations. In a real research environment, persist the exact
same JSON schema to an experiment tracker or append-only object store (for
example MLflow or a versioned Parquet dataset); neither replaces the disclosure
requirement, and both are production alternatives rather than evidence by
themselves.

## Evidence boundary and next question

This stage establishes no working signal, no expected return, and no live
tradability. It establishes that the later evaluator can see the search that
created a candidate. The null comparison is a diagnostic over this small,
survivorship-limited public-data exercise, not a proof that real market returns
are exchangeable. Next, [stage 02](../02-cross-sectional-rank/) turns a score
into a paper portfolio. That translation has its own choices and its own search
surface: the same signal with another sizing rule is another strategy.
