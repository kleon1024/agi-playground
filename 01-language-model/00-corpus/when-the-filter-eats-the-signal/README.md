---
status: verified
level: applied
base: scratch
label: When the filter eats the signal
verified: 2026-08-08
---

# When the wash eats the signal

**Question:** stage 00's funnel keeps 18.3% of raw web text, and [the
funnel shape](../the-funnel-shape/) attributes every drop to a gate. This
chapter asks the question the funnel cannot see: what happens when a gate
itself is wrong — when the quality filter was tuned on a slice of the
corpus that does not look like the slice it has to keep? The answer,
measured, is that a filter can remove the code-heavy tail of the signal
population at nearly the junk rate while keeping the same total removal
rate. The wash looks clean by count and is a silent disaster by class.

**Before this:** [stage 00's corpus](../README.md) for the five-gate
funnel and its measured survival rate, and [the funnel shape](../the-funnel-shape/)
for the drop-reason table that makes each gate accountable. This chapter
is the failure mode the funnel cannot see: a gate tuned on the wrong dev
slice.

## The wash, executed

The run ([record](runs/2026-08-08-filter-audit.md)) builds a 20,000-doc
population shaped like a crawl: 60% templated boilerplate, 40% signal, of
which 40% is a code-heavy slice. Code repeats keywords, so it has middling
word diversity and real repetition, plus a high symbol ratio — a
combination a quality filter can read as spam. Two weight sets remove the
same bottom 55% of the corpus by quality score:

| weights | removed by class | of the code-heavy slice | survivor code share |
|---|---|---|---|
| biased (symbol 0.45, length 0.05) | 9,508 junk + 1,492 signal (18.3% of signal) | 46.2% removed | 16% → 19% |
| balanced (symbol 0.20, length 0.20) | 10,988 junk + 12 signal (0.1% of signal) | 0.4% removed | 16% → 36% |

The two filters agree on how much they remove — 11,000 docs each. They
disagree on who gets removed. The drop audit shows why: the biased
filter's removed signal docs have mean symbol ratio 0.37 against 0.11 for
kept signal, and mean diversity 0.43 against 0.64. The symbol-ratio gate,
overweighted at 0.45, scored the code-heavy slice as spam; the repetition
gate agreed. The balanced filter, using the same four signals with
balanced weights, keeps 99.9% of the signal population and enriches code
from 16% to 36% of survivors.

## The failure mode, named

Quality filters are real, and they are threshold machines. Gopher trains a
classifier on roughly five thousand hand-labeled examples to filter its
web corpus (Rae et al., arXiv:2112.11446, Dec 2021); C4 applies heuristic
gates — capitalization, word counts, duplicates, bad-word lists — that
removed large fractions of Common Crawl (Raffel et al., arXiv:1910.10683,
Oct 2020); RefinedWeb and FineWeb show the same pattern at industrial
scale, with filter ablations that measurably change downstream performance
(Penedo et al., arXiv:2306.01116, Jun 2023; arXiv:2406.17557, Jun 2024).
Every one of these pipelines has thresholds tuned against a sample, and
the sample is chosen before the tuning starts.

The failure mode is that choice. When the tuning sample is unstratified —
junk-heavy and code-poor, or English-only while the pipeline serves mixed
text — the filter learns a correlation that is true in the dev slice and
false in the signal tail: symbol-heavy text is spam. The dev slice is free
because it is the corpus you already have; the gold labels are not,
because someone has to read documents per class to know which slice is
which. That asymmetry is the whole chapter: the cheap tuning path teaches
the filter the wrong correlation, and the expensive path is the only one
that sees it.

The code-heavy slice is the natural victim. Its signal is real — the
technical long tail a coding-capable model depends on — but its surface
looks like the junk the filter was built to remove: operators that read as
spam, repeated keywords that read as boilerplate, middling diversity that
reads as template. The filter cannot distinguish "looks like spam" from
"is spam" unless the tuning data taught it the difference. The sibling
chapter on [benchmark contamination](../when-the-benchmark-is-in-the-train-set/)
is the other half of the same problem: there, the corpus leaks into the
eval; here, the filter leaks the signal into the trash.

## The fix and its trade

The fix has three parts, and each one names its cost:

1. **Tune thresholds on a class-stratified gold holdout, not the free dev
   slice.** The balanced run uses the same four signals at balanced
   weights and keeps 99.9% of the signal population. The cost is the
   labels: a stratified holdout means reading documents per class, and the
   rarest class has to be a number, not a rumor — Gopher's five thousand
   labels is a scale, not a rule (Rae et al. 2021).
2. **Audit the drops per gate at release, not aggregate survival.** The
   funnel-shape drop-reason table exists; this chapter is the case-finding
   step it needs: every removed document gets a class and a gate, and the
   class is what exposes the mistake. The cost is a labeled sample of the
   removed set, maintained as the crawl's composition drifts.
3. **Watch the survivor distribution of the classes you care about.** The
   code-share shift (16% → 19% biased vs 16% → 36% balanced) is the cheap
   canary: if the filter is not neutral to a class, the class distribution
   moves when the filter changes. The cost is choosing the stratification
   before you see the number — the same trap as picking which metric is
   primary.

The trade, named: the free dev slice stops being free. Tuning on the gold
holdout costs label effort and calendar time, and the drop audit has to
re-run when the crawl shifts — FineWeb's ablations show filtering changes
downstream performance in either direction (Penedo et al. 2024), so a
filter that was right for last quarter's crawl is a hypothesis, not a
constant. You are buying the ability to see the 18.3% signal removal as a
number, instead of discovering it in eval after a model trained on what
the filter left behind.

## Who owns the loop

The wash is a data-health failure with a three-way handoff:

- **The data-pipeline team** owns gate thresholds and the composition of
  the dev slice they were tuned on, including the stratification decision:
  what classes the holdout represents and how many labeled examples the
  rarest class has.
- **The evaluation team** owns the class-stratified gold holdout and the
  per-gate drop audit — reading the removed set by class, not by total
  count — plus the survivor-shift check on the classes the product
  depends on.
- **The release owner** owns the funnel as a property: the survivor
  distribution is part of the release record, next to the drop-reason
  table, and a filter change that moves a class you care about is a
  product decision, not a pipeline detail.

When the ownership is implicit, the tuning happens on the free dev slice,
the drop audit never runs, and the code tail disappears from the corpus
without a number anywhere that says so.

## Evidence boundary

The executed read is one synthetic, fully labeled population over one seed
(20,000 docs, 60% junk, 40% code-heavy signal, 55% removal rate). It
demonstrates the mechanism — a threshold tuned on an unstratified slice
over-weights a signal that coincides with a minority class — and the
drop-audit shape that exposes it. The absolute rates do not transfer;
production rates come from running the same audit against the real crawl,
where the class labels are the expensive input. Measured funnel behavior
on real WARC data lives in stage 00's own runs
([core-vs-datatrove](../runs/2026-07-26-core-vs-datatrove.md),
[sample-and-distribution](../runs/2026-07-30-sample-and-distribution.md)).

## Check your mental model

Answer each before reading on.

**1. Why does the biased filter remove 18.3% of the signal population
while keeping the same 55% removal rate?**

Removal rate is a count, not a judgment. Both filters remove 11,000 docs;
the biased one spends that budget on the code-heavy slice because its
symbol-ratio gate, overweighted on a code-poor dev slice, scores those
docs as spam. The number that catches it is the drop audit by class, not
the aggregate.

**2. What makes the code-heavy slice look like junk to a quality filter?**

It repeats keywords, carries operators and punctuation, and has middling
word diversity — the exact surface the filter was built to remove. Only
the gold labels can tell "looks like spam" from "is spam," and the gold
labels are what the free dev slice does not have.

**3. What is the cheapest check that would have caught this before eval?**

The survivor-shift canary: record the per-class distribution of the corpus
before and after a filter change. Code share moves 16% → 19% when the
filter is wrong and 16% → 36% when it is right — the class distribution
tells you the filter is not neutral before you ever train a model.

## Next

Back to [stage 00's corpus](../README.md), where the funnel's next detour —
[the benchmark item is already in the training set](../when-the-benchmark-is-in-the-train-set/) —
is the contamination half of dirty-data washing. Together they cover the
two ways the corpus lies: it can lose the signal you need (this chapter)
or contain the eval you are about to test on (that one).
