---
status: verified
level: applied
base: scratch
label: The search log, read
verified: 2026-08-06
---

# The winner that did not survive the search

**Question:** [stage 01's signal research](../) searches hundreds of
variants. This chapter reads the recorded search and asks whether the best
signal is real or a multiple-testing artifact.

**Before this:** [stage 01's signal research](../) and its recorded search.

## The search, read

The run ([record](runs/2026-08-06-search-log-read.md)) reads the recorded
numbers:

| number | value |
|---|---|
| candidates logged | 32 |
| best in-sample IC | 0.0947 (momentum, 24-month) |
| null searches matching the winner | 95 of 300 |
| permutation p-value | 0.317 |

## Two readings

**The best signal is only real if it survives the search that found it.**
The harness evaluated 32 candidates, took the best, and then asked how
often a random permutation of forward returns would match or exceed it:
95 of 300 times. A p-value of 0.317 means the winner is indistinguishable
from what pure search over noise would produce — the observed 0.0947 IC is
what the best of 32 tries looks like by chance.

**The disclosed search log is what makes the correction possible.** The
run records all 32 candidates, not just the winner — the trial count the
deflated-Sharpe correction needs. A report that only kept the best variant
would have no way to price the search, which is why the log (32 JSONL
lines) and the correction are the same discipline: multiple testing is
only correctable if the search is disclosed.

## The fix and its trade

The fix is the disclosed search log plus the permutation null the stage
records: log all 32 candidates, then ask how often a no-edge search would
produce the winner (95 of 300 replicates, p = 0.317). That is the
deflated-Sharpe discipline's input — the trial count the correction
divides the winner's significance by (Bailey & López de Prado, "The
Deflated Sharpe Ratio," 2014; the multiple-testing problem in asset
pricing is documented in Harvey & Liu, "Backtesting," 2015).

The trade is a false-positive-versus-power decision. The null prices the
search this run actually performed: it answers "is this winner convincing
given 32 tries," not "is there an edge" — a genuinely weak but real signal
can fail the permutation null at low breadth, and the correction will not
tell the difference. The log costs a discipline (the researcher has to
keep every variant, including the embarrassing ones) and the permutation
pass costs compute, but the alternative is unpriced: a report that keeps
only the winner has no way to pay for the search, and its significance is
overstated by construction.

## Who owns the loop

- **Research** owns the search log: every candidate, not just the winner,
  written at search time. This is the input the deflation correction
  needs, and it cannot be reconstructed later from a report that kept one
  number.
- **Statistics/evaluation** owns the null: the permutation harness that
  prices the winner against the breadth that produced it, and the
  corrected significance that stage 03 consumes.
- **Stage 03's walk-forward** owns the handoff: it consumes the log and
  the trial count, and its deflated statistic is only as honest as the
  log's completeness.

When the log is implicit, the winner's 0.0947 IC is reported as a result
instead of what the null shows it to be — chance, a third of the time.

## Evidence boundary

The recorded signal search (32 candidates, 300 permutations, ten-name
public-data universe, one window). It reads that artifact; it does not
re-fetch and the p-value characterizes this search, not signal research in
general.

## Check your mental model

Answer each before opening it.

**1. The IC is 0.0947 — why is that not a result?**

<details>
<summary>Answer</summary>

Because the IC was selected as the best of 32 candidates. Selection bias
means the winner's number is inflated by how many tries produced it; the
permutation test prices exactly that inflation. 95 of 300 random searches
matched or exceeded 0.0947, so the observed IC is what chance produces a
third of the time — not evidence of a real edge.

</details>

**2. What would the deflated Sharpe need that the run provides?**

<details>
<summary>Answer</summary>

The number of variants searched — 32 here — which is what deflation
divides the winner's significance by. The run's disclosed search log is
what makes that count available to stage 03's correction; without it, the
multiple-testing price cannot be paid and the winner's significance is
overstated.

</details>

## Next

Back to [stage 01](../), or to
[when breadth inflates the winner](../when-breadth-inflates-the-winner/)
which reads the same search's selection-bias story.
