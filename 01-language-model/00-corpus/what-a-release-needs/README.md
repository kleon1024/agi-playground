---
status: draft
level: applied
base: none
label: What a release needs
---

# You have the text. What decides whether anyone can trust it?

[The previous chapter](../) ran 20,000 raw HTML responses through six gates and
kept 23.0% of them. That is a pipeline, and a pipeline is not yet a corpus
anyone else can use. Four decisions still sit unmade — how similar two
documents have to be before one of them is a duplicate, what proportions the
survivors get sampled in, what a labelled example has to carry, and what ships
alongside the tokens.

Each of those is a policy choice that a later result depends on, and each is
easy to make by accident. This chapter is the four of them, in the order the
corpus meets them.

**Before this:** [what has to be true of text before you train on it?](../),
through the measured funnel. The numbers below refer to that run's own shard.

## The duplicate threshold you set without meaning to

Exact hashing catches byte-identical copies. Web duplication is almost never
byte-identical — it is the same article under a different header, timestamp, or
navigation block. The from-scratch pipeline uses MinHash signatures over text
shingles, because for two shingle sets $A$ and $B$ a MinHash collision happens
at exactly the Jaccard similarity:

$$
P[h_{\min}(A)=h_{\min}(B)] = \frac{|A\cap B|}{|A\cup B|}
$$

One signature is a coin flip. The threshold comes from how the signature is
grouped: locality-sensitive hashing splits it into bands, and a pair becomes a
candidate if *any* band matches entirely.

**Worked, at the settings this corpus pipeline actually uses** — 64
permutations split into 16 bands of 4 rows, so the probability a pair is
compared at all is $1-(1-J^{4})^{16}$:

| true Jaccard $J$ | one band matches | pair is compared |
|---:|---:|---:|
| 0.9 | 0.656 | 100.0% |
| 0.7 | 0.240 | 98.8% |
| 0.5 | 0.063 | 64.4% |
| 0.3 | 0.008 | 12.2% |
| 0.1 | 0.0001 | 0.2% |

The half-way point sits at $(1/16)^{1/4} = 0.50$, exactly where 16 bands of 4
rows put it. That S-curve *is* the policy: near-copies at 0.9 are caught
essentially always, unrelated documents at 0.1 are examined twice in a
thousand, and the 0.5 row is where the corpus owner has to decide what counts
as a duplicate. Change 16 and 4 and you have moved the threshold whether or not
you meant to — which is why the band and row counts belong in the dataset
record, not only in the code.

The measured shard removed 264 near-duplicates from 4,856 candidate pairs. That
keep rate does not prove duplication is handled at web scale: the run compared
documents only within one bounded sample.

## What mixture are you actually training on?

A cleaned corpus is still a mixture of domains, languages, sources, and quality
bands, and sampling proportional to raw token count lets the largest source
decide the model. Fixed weights preserve smaller domains but can repeat them
enough to overfit. Either way the mixture has to be named and versioned:

```text
general web    0.55
code           0.20
reference      0.15
target domain  0.10
```

Those numbers are an illustration, not a recommendation — this repository
trained on one mixture and never compared it against another. The invariant is
that weights, token counts, and repetition rates are visible, because a model
change is uninterpretable if the mixture moved silently at the same time.
Whether a mixture change is even measurable is
[a separate question with its own harness](../../../foundations/05-is-the-difference-real/).

Curriculum scheduling changes those weights *during* training. Use it only when
the schedule answers a stated hypothesis — "high-quality reference text late in
training improves factuality without erasing coverage" — otherwise it is one
more uncontrolled variable in a run you will want to attribute later.

**Agentic data is a deliberate component, not a residue of this funnel.** The
gates above keep English prose; notebook cells, shell transcripts, and
tool-call logs are exactly the code- and list-heavy documents the language and
quality filters drop, so the web funnel produces almost none of the
action->error->inspect->fix arcs an agent needs. Programmes add those as a
separate, small component of the mix — reported practice is a single-digit
share of tokens, concentrated in the annealing phase, sourced from notebook
text already in the crawl plus synthesized or distilled tool-use and
SWE-style trajectories. [Mid-training](../../02-pretrain/mid-training/)
owns the trajectory formats, the separator and noise decisions, and the
evidence boundary; here it is one row of the mixture table, with a weight
that has to be named like any other.

## Labels are a second data product

Pretraining text needs a source and a filter record. Supervised, preference,
and verifiable-reward data each need more than that, and each fails
differently:

| Stage | Required record | Main failure |
|---|---|---|
| SFT | prompt, assistant response, template | prompt leakage, inconsistent style |
| Preference | prompt, chosen, rejected, rubric | annotator disagreement, position bias |
| RLVR | prompt, answer, deterministic verifier | rewarding a shortcut, not the task |

An annotation workflow needs written rubrics, calibration examples, measured
agreement, an adjudication path, and provenance. Synthetic data needs all of
that plus the generator version, the judge version, and the filters — "generated
by a strong model" is a description of the source, not a quality guarantee, and
[this repository measured how much the author changes the result](../../03-sft/distillation/which-teacher-changes-what/).

## Release a dataset, not a folder

What ships beside the tokens is what makes the corpus checkable by someone who
was not there:

1. source and consent scope;
2. extractor and filter versions, each rule with accepted and rejected counts;
3. a sample of the false positives and false negatives each rule produced;
4. content hashes and a stable dataset version;
5. train, validation, and test split policy;
6. contamination checks against every evaluation set;
7. sampled QA results and the known gaps.

Items 2 and 3 are what let a reader tell a *smaller* corpus from a *broken
extractor* — without them those two look identical from the outside.

Split by time or by source when random splitting would leak near-duplicate or
future content across partitions. And run the contamination checks **before**
training, not after: removing leaked data once you have already seen the
evaluation result no longer restores an unbiased estimate, because the choice
of what to remove was informed by the score.

## What this chapter does not establish

None of these four policies was compared against an alternative here. One
mixture was trained, one dedup threshold was used, no preference or RLVR
dataset was collected, and the corpus was never released to an outside reader
who could test whether the record is sufficient. The S-curve table is computed
from the band and row counts rather than measured, and the 264-of-4,856
duplicate figure is from a single bounded shard. What this chapter can tell you
is which decisions exist and what each one costs to get wrong; it cannot tell
you that this corpus got them right.

Primary references: Broder (1997) for MinHash; Indyk & Motwani (1998) for LSH;
Gebru et al., *Datasheets for Datasets* (2018) for the release record.

## Check your mental model

1. You raise the LSH band count from 16 to 32, keeping 4 rows. Which way does
   the duplicate threshold move, and what does it cost?

<details>
<summary>Answer</summary>

Down — more bands means more chances for one of them to match, so pairs at
lower true similarity become candidates. The half-way point moves from
$(1/16)^{1/4} = 0.50$ to $(1/32)^{1/4} \approx 0.42$. The cost is on both
sides: more candidate pairs to compare, so more compute, and more documents
removed that a reader might not consider duplicates at all. It is a corpus
policy decision wearing the clothes of a tuning parameter, which is exactly why
the band and row counts have to appear in the dataset record.

</details>

2. Your model regressed after a data change and you want to know why. What in
   the corpus record makes that answerable, and what makes it unanswerable?

<details>
<summary>Answer</summary>

Answerable if the mixture weights, token counts, repetition rates, filter
versions, and dataset version are all recorded and only one of them changed —
then the regression has a named candidate cause. Unanswerable if the mixture
moved at the same time as the filters, or if either changed without a version
bump, because the model difference now has more than one possible owner and no
record separates them. This is the same discipline as an architecture ablation:
one variable at a time, and everything else disclosed.

</details>

3. You discover an evaluation item in your training corpus after reading the
   scores. Why is removing it and re-running not a full fix?

<details>
<summary>Answer</summary>

Because the decision of what to remove was made after seeing the result, so the
re-run is no longer an unbiased estimate — you have selected the removal in a
way that is correlated with the score you are trying to measure. The clean
version of this is to run contamination checks before training and to keep a
private held-out set that development never touches. After the fact, the honest
move is to disclose the contamination and what was checked, and to treat the
re-run as evidence with a stated caveat rather than as a clean number.

</details>

## Next

**Continue the mission at [stage 01 — tokenizer](../../01-tokenizer/)**, which
takes this corpus and fixes the vocabulary every later token ID depends on.

If the open question is whether a data change is measurable at all, that is
[is the difference real?](../../../foundations/05-is-the-difference-real/) —
paired runs across seeds, and why one run per arm is not a result.
