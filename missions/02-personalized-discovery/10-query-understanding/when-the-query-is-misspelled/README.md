---
status: verified
level: applied
base: scratch
label: When the query is misspelled
verified: 2026-08-06
---

# Where normalization stops and correction must begin

**Question:** [stage 10's query understanding](../) normalizes case,
punctuation, and stopwords. This chapter reads the executed tokenizer and
asks where normalization fails.

**Before this:** [stage 10 — query understanding](../) and its executed
pipeline.

## The variants, executed

The run ([record](runs/2026-08-06-misspelled-read.md)) executes the
stage's own tokenizer over four spellings:

| query | exact-match on "headphones" |
|---|---|
| wireless headphones | True |
| wireless heaphones | False |
| wireless hedphones | False |
| wirless headphones | True |

## Two readings

**Normalization fixes the noise it was built for — case, punctuation,
stopwords.** "Headphones" and "headphones" become the same token; "the"
and "to" drop out. Without this, the index would be split by
representation, and the same query would match different keys.

**A misspelling changes the token itself, and no normalization repairs
it.** "heaphones" and "hedphones" never become "headphones" — the token
is different, so exact-match retrieval fails. The fix is either query
correction (edit distance to the nearest index term) or a retrieval
matcher tolerant of near-misses. The boundary is the lesson: normalization
handles how the word is written, correction handles how it is spelled.

## Evidence boundary

The executed variants over four hand-built spellings (illustrative,
deterministic). It demonstrates the boundary; real query correction needs
a vocabulary and an edit-distance or learned matcher.

## Check your mental model

Answer each before opening it.

**1. Why does "wirless" still match while "heaphones" does not?**

<details>
<summary>Answer</summary>

Because the misspelling is in a different token. "Wirless" is a variant
of "wireless", and the query still contains the exact "headphones" token
— so exact-match on the index term succeeds. "Heaphones" misspells the
index term itself, and no token in the query equals it. The boundary is
per-token: normalization and correction both operate on terms.

</details>

**2. What would retrieval need to fix a misspelled index term?**

<details>
<summary>Answer</summary>

Either correct the query first (map "heaphones" to "headphones" via edit
distance or a learned model), or match by near-miss (retrieve terms
within edit distance). Both move the work into query understanding,
because a ranker downstream only sees the tokens it was handed. The
misspelling must be repaired before retrieval, not after.

</details>

## Next

Back to [stage 10](../), or forward to
[stage 11 — search retrieval](../../11-search-retrieval/) where the
normalized query hits the index.
