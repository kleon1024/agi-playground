---
status: draft
---

# 02 — Data

**Question:** how does a raw crawl become a training corpus without silently
changing what the model is being trained to learn?

We will follow one concrete artifact: 40,000 HTML responses from Common Crawl.
The published run processed the same input through a readable local pipeline
and a DataTrove FineWeb-style recipe. The local path kept 9,184 documents;
the stricter production recipe kept 5,513. The difference, not the larger
number, is the lesson.

The output of this chapter is not “clean text.” It is a versioned dataset with
a manifest, stage-level rejection reasons, sampled false-positive audits, and
a contamination policy.

## 1. Define eligibility before quality

A crawl contains redirects, binary responses, extraction failures, many
languages, navigation fragments, duplicated templates, and useful prose. The
first question is not whether a page is “good.” It is whether the page is even
eligible for this corpus.

The measured local funnel started as follows:

```text
20,000 HTML responses
18,210 non-empty extractions
 7,348 English documents
```

Language filtering removed more documents than all local quality heuristics
combined. That means “an English corpus” is already a major distribution
choice. A model trained on the survivors cannot represent languages that the
eligibility gate removed, regardless of later model scale.

For every eligibility rule, record:

- the rule and its version;
- documents accepted and rejected;
- a sample of false positives and false negatives;
- the policy reason for the rule.

Without these records, a smaller final corpus cannot be distinguished from a
broken extractor.

## 2. Separate extraction failure from content failure

HTML-to-text extraction owns layout interpretation. Quality filtering owns the
resulting text. Combining them hides the source of loss.

In the local run, 1,790 responses became empty during extraction. In the
DataTrove comparison, Trafilatura consumed 85% of total runtime. These are
system facts with different owners:

```text
empty output -> extraction correctness
slow output  -> extraction performance
bad prose    -> downstream quality policy
```

A replacement extractor is acceptable only if it preserves or improves the
measured text yield and sampled quality, not merely if it runs faster.

## 3. Remove failure modes, not documents

Quality rules should name the behavior they are preventing:

- extreme mean word length catches corrupted or concatenated text;
- symbol and hash ratios catch navigation or markup residue;
- line-level C4 rules remove boilerplate fragments;
- repetition filters catch loops and templated spam.

The local pipeline kept 6,349 documents after Gopher-style rules and 4,856
after line filtering on the first WARC file. DataTrove was stricter because it
also used repetition and FineWeb quality filters. Calling one pipeline “better”
from survivor count alone would be invalid. The missing evidence is downstream
quality and a review of rejected examples.

This is why every gate needs its own rejection sample. Aggregate corpus size
cannot tell you which useful data was discarded.

## 4. Deduplicate after normalization

Exact hashing catches byte-identical copies. Web duplication is usually near
duplication: a shared article with a different header, timestamp, or navigation
block. The readable pipeline uses MinHash signatures over text shingles and
locality-sensitive hashing to avoid comparing every pair.

For two sets $A$ and $B$, MinHash preserves Jaccard similarity in expectation:

$$
P[h_{\min}(A)=h_{\min}(B)] = \frac{|A\cap B|}{|A\cup B|}
$$

LSH groups the signature into bands. More bands increase recall and false
positives; more rows per band increase precision and false negatives. The
threshold is therefore a corpus-policy decision, not an implementation detail.

The first measured shard removed 264 near duplicates from 4,856 candidates.
That high keep rate does not prove duplicates are solved at web scale: the
local run only compared documents within a small bounded sample.

## 5. See how the gates compound

The next control uses rounded retention rates from the measured local funnel.
Change one gate at a time. Before moving the slider, predict whether a
ten-point change upstream or downstream will remove more final documents.

<!-- interactive: DataCurationFunnel -->

The gates multiply. A strict eligibility choice reduces the population every
later quality rule can inspect. Therefore a single “documents kept” KPI is not
a quality objective. The release needs stage-level yield plus false-rejection
audits.

## 6. Choose the training distribution explicitly

After cleaning, a corpus is still a mixture of domains, languages, sources,
and quality bands. Sampling proportional to raw token count lets the largest
source dominate. Fixed source weights preserve smaller domains but can repeat
them enough to cause overfitting.

Represent the mixture as named, versioned weights:

```text
general web    0.55
code           0.20
reference      0.15
target domain  0.10
```

These numbers are an example, not a recommendation. The invariant is that
weights, token counts, and repetition rates are visible. A downstream model
change is uninterpretable if the mixture changed silently at the same time.

Curriculum scheduling changes those weights during training. Use it only when
the schedule answers a hypothesis such as “high-quality reference text late in
training improves factuality without erasing broad coverage.” Otherwise it is
another uncontrolled variable.

## 7. Treat labels as another data product

Supervised fine-tuning, preference optimization, and verifiable-reward RL each
need a different contract:

| Stage | Required record | Main failure |
|---|---|---|
| SFT | prompt, assistant response, template | prompt leakage or inconsistent style |
| Preference | prompt, chosen, rejected, rubric | annotator disagreement or position bias |
| RLVR | prompt, generated answer, deterministic verifier | rewarding a shortcut instead of the task |

An annotation workflow needs written rubrics, calibration examples, agreement
measurement, adjudication, and provenance. Synthetic data needs the same
contract plus generator version, judge version, and filters. “Generated by a
strong model” is not a quality guarantee.

## 8. Release a dataset, not a folder

A releasable dataset contains:

1. source and consent scope;
2. extractor and filter versions;
3. stage counts and rejection reasons;
4. content hashes and a stable dataset version;
5. train, validation, and test split policy;
6. contamination checks against every evaluation set;
7. sampled QA results and known gaps.

Split by time or source when random splitting would leak near-duplicate or
future content across partitions. Contamination checks must run before model
training, because removing leaked data after seeing evaluation results no longer
restores an unbiased estimate.

## Run the working example

The complete executable path is
[Mission 01, stage 00](../../missions/01-language-model-agent/00-corpus/).
It contains:

- a readable WARC-to-shard pipeline;
- the DataTrove comparison recipe;
- the exact commands and stage counts;
- the limitations of the bounded local run.

The comparison establishes that both pipelines execute and that their policies
produce different funnels. It does not establish which corpus trains the
better model. That question requires a controlled pretraining comparison.

## Check your mental model

1. Why is language filtering an eligibility decision rather than a quality
   score?
2. Which evidence distinguishes a strict filter from a broken extractor?
3. Why can a lower dedup threshold improve recall while harming precision?
4. Why are final corpus size and downstream model quality not interchangeable?
5. What must remain fixed to attribute a model change to the data mixture?

## Next

The output is a tokenizable, versioned corpus. Continue to
[pretraining](../training/), where vocabulary, model size, optimizer state, and
token budget must be chosen against that artifact.

Primary references: Common Crawl, FineWeb, DataTrove, Lee et al. on deduplication,
Gopher data filtering, Dolma, DataComp-LM, DPO, and Tulu 3.
