---
status: verified
level: applied
base: scratch
label: When the output cannot be parsed
verified: 2026-08-07
---

# The text answer is not a list

**Question:** [stage 31's LLM ranking](../) emits a reordered list,
but it emits it as text. This chapter asks what happens when the text
is not a valid permutation — a duplicated ID, a skipped ID, an ID
outside the candidate set — and compares the parse that silently
accepts it with the check that repairs it.

**Before this:** [stage 31 — LLM ranking](../) and its prompt-order
audit, which showed the tail reorder swinging with prompt order. This
detour is the second failure surface of the same ranker: even a stable
answer can fail to be a list.

## The parse failure, executed

The run ([record](runs/2026-08-07-output-parse-read.md)) parses a
12-response cohort two ways:

| path | clean | damaged | docs dropped | phantoms served | extra cost |
|---|---:|---:|---:|---:|---:|
| naive parse | 7 | 5 of 12 | 5 | 1 | none |
| validate + resample | 12 | 0 of 12 | 0 | 0 | 5 inference calls |

Failure shapes: 2 duplicate-ID answers, 2 missing-ID answers, and 1
answer carrying an ID outside the candidate set.

## The reading

The text answer is not a list. A parser that accepts the text
silently ships a shorter or wider list — 5 of 12 reorders serve a
damaged list: five documents dropped and one phantom ID that no user
can reach. The fix is structural, not linguistic: check uniqueness,
check membership in the candidate set, check completeness, and only
then serve the ranking. The resample repairs every invalid response by
keeping the valid prefix and appending the missing documents in
pointwise order — at a measured cost of one extra inference call per
invalid response. That cost is why the parse check belongs before the
LLM call's result is trusted, not after the damage ships.

## The fix and its trade

The fix is structural validation before the ranking is served: check
uniqueness, membership in the candidate set, and completeness, and
repair an invalid answer by keeping the valid prefix and appending the
missing documents in pointwise order. The executed cohort prices the
failure — the naive parse ships a damaged list for 5 of 12 responses
(five documents dropped and one phantom ID nobody can reach), while the
validate-and-resample path repairs all five at a measured cost of one
extra inference call per invalid response.

The trade is latency against correctness: each resample adds an
inference call to the exact budget stage 31 names, and when the invalid
rate is high, the cheaper fix is to distrust the format entirely and
fall back to the pointwise order. The repair is structural rather than
linguistic because the failure shapes are mechanical — a duplicate ID
drops a document while keeping the list length, so no position-count
check notices, and only a check against the candidate set catches it.

## Who owns the loop

- **The serving and inference team** owns the parse, the validation
  check, and the fallback to the pointwise order when the invalid rate
  is high.
- **The ranking and model team** owns the prompt's output format and
  the resample rule that repairs an invalid answer.
- **The evaluation team** owns the invalid-rate measurement from logged
  responses, the number that decides resample versus fallback.

## Evidence boundary

The executed cohort over twelve hand-built raw answers (illustrative,
deterministic, no real LLM inference). It demonstrates the failure
shapes and the repair; real parse failure rates come from logged
responses of the actual model, which is exactly the log the
[prompt-order audit](../runs/2026-08-07-rank-order-audit.md) format
exists to collect.

## Check your mental model

Answer each before opening it.

**1. Why is a duplicate ID worse than a missing ID in the same answer?**

<details>
<summary>Answer</summary>

A missing ID drops one document; a duplicate ID silently drops a
document while keeping the list length, so no position-count check
notices. The executed cohort shows both: the duplicate answers lose a
document each while the list still names five IDs. Completeness has to
be checked against the candidate set, not against the answer's length.

</details>

**2. What does the resample trade for its repairs?**

<details>
<summary>Answer</summary>

One extra inference call per invalid response. The repair keeps the
valid prefix and appends the missing documents in pointwise order, so
it restores completeness at the cost of latency — the exact budget
[stage 31](../) names. When the invalid rate is high, the cheaper
fix is to distrust the format and fall back to the pointwise order
entirely.

</details>

## Next

Back to [stage 31](../), where the LLM reorders the list it can afford
to see — now with the checks that decide whether the emitted text is
actually a ranking.
