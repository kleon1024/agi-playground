# Run — the filter that eats the signal, measured by class

**Date:** 2026-08-08
**Command:** `uv run python core/filter_audit.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.06s.
**Cost:** \$0 (local lane).

## Purpose

Stage 00's wash is a set of quality gates — language, diversity, symbol
ratio, length, repetition — and every gate is a threshold someone tuned.
This run asks what happens when a gate is tuned on the wrong slice of the
corpus: a dev sample that happens to be junk-heavy and code-poor teaches
the filter that symbol-heavy text is spam, and the filter then removes the
code-heavy tail of the signal population at nearly the junk rate. The
population is synthetic but shaped like a crawl: 60% templated boilerplate
(low diversity, low symbol ratio, high repetition) and 40% technical
long-tail signal split into prose-like docs and a code-heavy slice (code
repeats keywords, so it has middling diversity and real repetition, plus a
high symbol ratio that a quality filter can read as spam). Two weight sets
remove the same bottom 55% of the corpus; the audit then measures what was
removed by gold class, how the survivor distribution shifted, and a per-gate
drop audit that names which gate eats the signal.

## Output

```
population: 20000 docs, 40% signal (of which 40% code-heavy), removal rate 55%

biased weights (symbol 0.45, length 0.05) -- tuned on a
junk-heavy, code-poor dev slice:
  removed 11000 docs = 9508 junk (80.3%) + 1492 signal (18.3%)
  removed set is 13.6% signal; signal kept 81.7% (46.2% of code-heavy signal removed)
  survivor shift: diversity 0.39 -> 0.55, length 0.39 -> 0.52, code share 16% -> 19%
  drop audit of removed signal docs: mean symbol ratio 0.37 (kept signal 0.11, removed junk 0.03), mean diversity 0.43 (kept 0.64)

balanced weights (symbol 0.20, length 0.20) -- tuned on a
class-stratified gold holdout:
  removed 11000 docs = 10988 junk (92.8%) + 12 signal (0.1%)
  removed set is 0.1% signal; signal kept 99.9% (0.4% of code-heavy signal removed)
  survivor shift: diversity 0.39 -> 0.57, length 0.39 -> 0.58, code share 16% -> 36%
  drop audit of removed signal docs: mean symbol ratio 0.39 (kept signal 0.16, removed junk 0.03), mean diversity 0.37 (kept 0.60)

verdict: at the same 55% removal rate the biased filter
removes 18.3% of the signal population vs 0.1% for the balanced one -- 46.2% of the code-heavy slice against
0.4%.
The drop audit shows what the removed signal docs are: mean
symbol ratio 0.37 against 0.11 for kept signal -- the filter
removed the code-heavy slice, whose high symbol ratio the biased
weights scored as spam. A wash that looks clean by total count is
a wash that removed the code tail; the class-stratified audit is
the only thing that sees it.
```

## Reading the output

- **Same removal rate, different victim.** Both filters removed exactly
  11,000 docs (55% of the population). The biased filter ate 1,492 signal
  docs (18.3% of the signal population); the balanced one ate 12 (0.1%).
  Total-removal-rate alone cannot see the difference — the case-finding
  step needs the gold class labels.
- **The code-heavy slice is the eaten tail.** The biased weights removed
  46.2% of the code-heavy signal; the balanced weights removed 0.4%. The
  survivor code share tells the same story: biased 16% → 19% (code barely
  survives), balanced 16% → 36% (code is enriched).
- **The drop audit names the mechanism.** Removed signal docs in the biased
  run have mean symbol ratio 0.37 against 0.11 for kept signal — the
  symbol-ratio gate, overweighted at 0.45, scored the code-heavy slice as
  spam. Diversity explains the rest: removed signal diversity 0.43 vs 0.64
  kept, so the repetition gate also contributed.
- **Deterministic.** Fixed seed 11; rerunning reproduces the numbers.

## Evidence boundary

The population is synthetic and labeled, which is exactly what a real crawl
does not give you — gold class labels are the expensive thing this run
assumes you have. The mechanism (threshold tuned on an unstratified dev
slice over-weights a signal that coincides with a minority class) transfers
to real quality filters; the absolute rates do not. For measured real-corpus
filter behavior, the stage links the funnel run
`runs/2026-07-26-core-vs-datatrove.md` and the sampling run
`runs/2026-07-30-sample-and-distribution.md`, plus dated external results
(Gopher quality classifier, C4 filter, RefinedWeb, FineWeb).
