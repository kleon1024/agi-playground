---
status: verified
level: applied
base: scratch
label: The funnel shape
verified: 2026-08-06
---

# 18.3% of the raw web survives — and that is the point

**Question:** [stage 00's corpus](../) cleans raw Common Crawl through a
five-gate funnel. This chapter reads the recorded 3,000-document sample
and asks what the funnel's shape actually is.

**Before this:** [stage 00's corpus](../) and its recorded sample run.

## The funnel, read

The run ([record](runs/2026-08-06-funnel-read.md)) reads the recorded
stages:

| gate | docs | % of raw |
|---|---:|---:|
| text extracted | 2,699 | 90.0% |
| english | 947 | 31.6% |
| gopher quality | 755 | 25.2% |
| c4 line filter | 569 | 19.0% |
| minhash dedup | 550 | 18.3% |

## Two readings

**The funnel is the audit trail — every gate's decision is attributable.**
The recorded drop-reason table names each rejection: 1,752 not-English,
301 extraction-empty, 186 empty-after-C4, 97 low-alpha, and so on. A
corpus whose cleanliness is a single number cannot be audited; one whose
drop reasons are counted can. The funnel shape is the accountability.

**The shape is stable across runs, which is what makes it a property.**
The 3,000-document sample's English survival (31.6%) and dedup survival
(96.7%) are broadly consistent with the 20,000-document run (36.7%,
94.6%) — the small differences are sampling variance, not contradiction.
Two samples agreeing on the shape is what turns "the funnel works" from a
claim into a measured property of the pipeline.

## Who owns the loop

The funnel shape is a data-health property with a three-way handoff:

- **The data-pipeline team** owns the gates and the drop-reason table:
  each gate's threshold, each rejection class, and the sample the gate
  was tuned on. It owns the funnel as a reproducible artifact.
- **The evaluation team** owns the drop-reason audit: reading the removed
  set by rejection class, not by total count, and checking that the class
  mix of what survives still matches what the product needs.
- **The release owner** owns the shape as a property: the 18.3% survival
  rate and the per-gate drop distribution are part of the release record,
  and a gate change that moves them is a product decision, not a pipeline
  detail.

When the ownership is implicit, the funnel is a single number, the drop
reasons go unread, and a gate that silently eats a class the product needs
stays invisible until eval.

## The fix and its trade

The fix is the drop-reason table itself, executed: every rejection gets a
class, every class gets a count, and the gate that drops the most is the
one worth scrutinizing first. The trade is the table's maintenance cost —
each new gate, threshold, or crawl segment re-runs the read and re-checks
that the class mix of the survivors still matches what the model will be
asked to do, which is why the funnel is read on a fresh sample, not a
frozen one. The deeper failure — a gate tuned on the wrong slice removing
an entire class while the total rate looks fine — is the next detour,
[when the filter eats the signal](../when-the-filter-eats-the-signal/).

## Evidence boundary

The recorded 3,000-document sample (one WARC, one seed, one crawl
segment). It reads that artifact; it does not re-download and the
percentages characterize this sample.

## Check your mental model

Answer each before opening it.

**1. Why does the funnel report percentages of raw at every gate?**

<details>
<summary>Answer</summary>

Because each gate's cost is a different question. "31.6% of raw HTML is
English" says the language gate removes most of the crawl; "79.7% kept"
at the next gate says gopher-quality removes a quarter of what English
left. Reporting both the cumulative and per-gate view is what lets a
reader see which gate does the heavy lifting — here, English, at 31.6%.

</details>

**2. What does the drop-reason table add that the counts alone do not?**

<details>
<summary>Answer</summary>

It makes each rejection explainable. The counts say 947 documents are
kept; the table says why the other 2,053 are not — not-English dominates
(1,752), extraction failures are next, and the rest are quality filters.
That distribution is what a corpus owner needs to tune: the gate that
drops the most is the one worth scrutinizing first.

</details>

## Next

Back to [stage 00](../), or to
[what a release needs](../what-a-release-needs/) which reads the same
stage's versioning contract. The funnel's hidden failure — a gate tuned on
the wrong slice removing a whole class at an unchanged total rate — is
[when the filter eats the signal](../when-the-filter-eats-the-signal/).
