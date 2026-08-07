---
status: verified
level: applied
base: scratch
label: Benchmark contamination
verified: 2026-08-07
---

# The benchmark item is already in the training set

**Question:** the release record in [what a release needs](../what-a-release-needs/)
lists contamination checks as a required item. This chapter executes
them: a benchmark leaks into the training corpus at three edit levels —
verbatim copies, near copies, and paraphrases — and four detectors read
against the leak. The question is which detector catches which leak, and
what the leak teaches the model even when no detector fires.

**Before this:** [stage 00's corpus](../) for the cleaning funnel the
leak survives, and [what a release needs](../what-a-release-needs/) for
the release record that demands the check. This chapter is the check,
executed.

## The leak, detected

The run ([record](runs/2026-08-07-contamination-read.md)) builds a
200-item synthetic benchmark, leaks 60 items into a 460-document corpus
(20 verbatim, 20 near copies at measured Jaccard 0.57, 20 paraphrases),
and runs the four checks real pipelines run before release:

| detector | exact | near | paraphrase | background FP |
|---|---:|---:|---:|---:|
| exact hash | 20/20 | 4/20 | 0/20 | 0/400 |
| 13-gram overlap | 20/20 | 19/20 | 0/20 | 0/400 |
| MinHash, threshold 0.7 | 20/20 | 13/20 | 0/20 | 0/400 |
| MinHash, threshold 0.5 | 20/20 | 17/20 | 0/20 | 0/400 |

The 13-gram overlap heuristic — any 13-token sequence shared with a
benchmark item flags the document — is the workhorse (Brown et al.,
"Language Models are Few-Shot Learners," NeurIPS 2020, arXiv:2005.14165):
it catches 19 of 20 near copies with zero false positives. Exact hashing
catches only verbatim copies. MinHash near-duplicate detection (Lee et
al., "Deduplicating Training Data Makes Language Models Better," ACL
2022) is a recall dial: the verification threshold decides whether a
0.57-Jaccard copy is a duplicate or not.

## The leak, taught

Detection is only half the story. The inflation pass asks how many
benchmark answers the corpus teaches at all — the memorization measure
of Carlini et al. ("Extracting Training Data from Large Language
Models," USENIX Security 2021):

| corpus | strong signal (subject + answer + property) | fact-level (subject + property) |
|---|---:|---:|
| clean | 0/200 | 0/200 |
| contaminated | 40/200 | 60/200 |

The verbatim and near copies leak the answer line itself (40/200 at the
strong signal). The paraphrases evade every detector — 0/20 across all
four — yet still teach their 20 facts, which is why fact-level recovery
reaches 60/200. That is the dangerous case: a paraphrased benchmark item
in the crawl looks like ordinary web text, no check flags it, and the
model still memorizes the answer.

## Who owns the loop

Contamination is a data-health failure with a three-way handoff:

- **The data team** owns the check as part of the release record: the
  exact hash, the 13-gram pass, and the MinHash near-duplicate pass
  against every eval set, run **before** training. It owns the layered
  detector stack and the false-positive read.
- **The evaluation team** owns the consequence: benchmark numbers are
  only trusted with the contamination report attached, and the private
  held-out set that development never touches stays the source of the
  unbiased estimate.
- **The release owner** owns the disclosure. When overlap is found after
  the fact, the honest move is to disclose it, not to silently re-run:
  the decision of what to remove was made after seeing the score, so the
  re-run is no longer an unbiased estimate.

When the ownership is implicit, the benchmark number ships without its
contamination report, the paraphrase leaks are invisible to every
detector, and the eval stops measuring the model and starts measuring
the overlap.

## The fix and its trade

The fix is the layered stack, run before training: exact hash for verbatim
copies, the 13-gram overlap pass for near copies, MinHash at a stated
threshold for the duplicate dial, and a disclosure record for what the
detectors cannot see. The trade is the false-positive budget and the
recall dial: the 13-gram pass runs at zero background false positives on
this read, but a real corpus is not 460 documents — its background
false-positive rate is the number that decides whether the pass can run
unattended or needs human review of every flag. Lowering the MinHash
threshold catches more near copies (17/20 at 0.5 vs 13/20 at 0.7) by
flagging more ordinary duplicates, and every flag a human has to read
costs the pipeline time it could spend elsewhere. The part no detector
trades away is the paraphrase: it evades all four checks, so the fix's
real cost is the private held-out set that development never touches, kept
uncontaminated by construction rather than by detection.

## Evidence boundary

The executed synthetic read over one seed (200 items, 60 leaks at three
edit levels, 460 docs). It demonstrates the detection rates and the
inflation mechanism; production overlap rates come from running the same
four checks against the real eval sets and the real corpus before
release, where the background false-positive rate is the number that
decides which detectors can run unattended.

## Check your mental model

Answer each before opening it.

**1. Why is the paraphrase the dangerous leak, and not the verbatim
copy?**

<details>
<summary>Answer</summary>

Because the verbatim copy is caught by every detector, while the
paraphrase is caught by none — yet both teach the answer. The executed
read shows paraphrase detection at 0/20 across all four methods while
fact-level recovery still counts its 20 items. A detector stack that
only looks for copies cannot see the leak that matters.

</details>

**2. Why does removing a leaked item after seeing the score not restore
an unbiased estimate?**

<details>
<summary>Answer</summary>

Because the removal decision was informed by the score: you removed
exactly the items that correlated with the result, which is selection.
The clean version is to run the contamination checks before training and
to keep a private held-out set. After the fact, the honest move is
disclosure with a stated caveat, not a silent re-run.

</details>

## Next

Back to [what a release needs](../what-a-release-needs/), where the
release record's item 6 — contamination checks — now has an executed
form. The funnel itself is read in [the funnel shape](../the-funnel-shape/).
