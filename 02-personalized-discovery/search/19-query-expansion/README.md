---
status: verified
level: applied
base: scratch
label: Query expansion
verified: 2026-08-07
---

# The correction that decides which query you meant

**Question:** [stage 10's query understanding](../10-query-understanding/)
normalizes a raw string, but normalization cannot repair a misspelling.
This stage asks what correction is for, and answers: retrieval
pre-processing whose value is measured by the recall it recovers.

**Before this:** [stage 10 — query understanding](../10-query-understanding/)
for normalization, and [stage 11 — search retrieval](../11-search-retrieval/)
for the BM25 index the corrected query has to hit.

## The correction, executed

The run ([record](runs/2026-08-07-query-expansion.md)) measures the edit
distance from the raw query `heaphones` to candidate catalog terms:

| candidate | edit distance |
|---|---:|
| headphones | 1 |
| headsets | 5 |
| shoes | 5 |
| shorts | 6 |
| flights | 7 |

Corrected query: `headphones`. BM25 on the raw query matches nothing in
the index; the corrected query matches the catalog.

## The mechanism, named

Correction is a retrieval-stage repair, not a query-side nicety. The
edit distance says how far each candidate is; the retrieval test says
whether the corrected query recovers documents the raw query lost. The
value of a correction is the recall it recovers — a correction that
retrieves nothing is decoration, whatever its distance score looks
like.

The distance table is also why correction is a decision rather than a
rule: when one candidate is one edit away, the repair is cheap; when
several candidates are near, the correction needs a context signal —
which is where [the expansion detour](when-expansion-hurts/) shows the
precision price.

## Why this belongs in the mission

Stage 10 normalized the query; stage 11 built the lexical index. This
stage is where a raw string that normalization cannot fix gets repaired
before it ever reaches the index — the search analogue of recall, where
[stage 02's rule](../../shared/02-recall/) applies: a perfect ranker cannot rank
an item that was never retrieved.

## How you find it: the expansion-lift audit, executed

Correction is measured by recall, but recall over which queries? The
failure mode the aggregate hides is expansion that lifts nothing while
costing precision — and the aggregate cannot see it, because head
queries dominate the average. The run
([record](runs/2026-08-07-expansion-audit.md)) emits a 24-query log —
12 head queries the catalog already covers, 12 tail queries with
vocabulary mismatches — and stratifies the recall lift:

| stratum | queries | base recall | expanded recall | lift | noise/query |
|---|---:|---:|---:|---:|---:|
| head | 12 | 1.000 | 1.000 | +0.000 | 1.00 |
| tail | 12 | 0.350 | 0.817 | +0.467 | 0.33 |

The verdict is EXPANSION LIFT CONCENTRATED IN THE TAIL: the aggregate
reports a +0.233 recall lift as if it applied everywhere, but every
unit of it is a tail repair, and head queries recover nothing while
taking on 1.00 irrelevant hit each. Xu and Croft ("Query Expansion
Using Local and Global Document Analysis", SIGIR 1996) showed local
(per-query) analysis beats global expansion for exactly this reason —
the benefit is query-dependent, which is what the stratification makes
visible. The decision that follows is to gate expansion by stratum, not
to ship it everywhere on the strength of the average.

## Who owns the loop

The expansion changes what retrieval is allowed to see; someone must own
what each expansion commits the system to, and the handoffs are where
expansion fails:

- **The query-understanding or expansion team** owns the expansion
  policy: which terms expand, which synonyms are trusted, and the
  stratum gate that stops head queries from being widened. It owns the
  precision cost, and the when-expansion-hurts detour is its failure
  mode.
- **The retrieval team** owns the candidate set the expansion feeds:
  whether the widened query recovers documents the raw query lost, and
  what noise the index then has to outrank. It owns the recall
  consequence, and the when-the-correction-helps detour is its
  evidence.
- **The data or logging team** owns the evidence that correction is
  even possible: the query log that separates head from tail, and the
  click evidence that catches the errors strings cannot — the
  real-word typo. It owns the log, and the when-the-typo-is-a-real-word
  detour is its failure mode.

When the ownership is implicit, the expansion team ships synonyms, the
retrieval team trusts the widened query, and nobody owns the head/tail
split — so head traffic pays precision for a lift that lives entirely
in the tail, and the aggregate report says the system improved.

## Evidence boundary

The executed distance table over one misspelling and five candidates
(illustrative, deterministic). It demonstrates the mechanism; real
correction also needs candidate generation from the catalog and a
language prior over which candidate the user meant.

## Check your mental model

Answer each before opening it.

**1. Why is correction measured by recall, not by edit distance?**

<details>
<summary>Answer</summary>

Because the goal is retrieval. Edit distance only says how far each
candidate is; the retrieval test says whether the corrected query finds
documents the raw query lost. A correction that produces a nice-looking
query but no recovered documents has changed nothing — the value lives
at the index, not in the string.

</details>

**2. When should the system leave the query alone?**

<details>
<summary>Answer</summary>

When the candidates are all far, or when several senses compete. If the
nearest term is many edits away, the user may not have meant any
catalog term; if the term is ambiguous, correction can push the query
toward the wrong sense. The expansion detour shows exactly that cost —
correction needs a prior over what the user meant, not just a distance
table.

</details>

## Next

Forward to [stage 20 — dense retrieval](../20-dense-retrieval/) where
the corrected query meets a meaning-based index.

A detour from here: [correction recovers what the raw query could
not](when-the-correction-helps/) — the executed recovery read: the raw
query `heaphones` retrieves zero documents while the corrected
`headphones` retrieves three, so the correction is priced in recall.

Another detour: [expansion trades precision for recall](when-expansion-hurts/) — the executed ambiguity read: expanding `apple` adds no new
relevant hits, only the wrong senses, so expansion needs a sense
signal.

And a third: [the misspelling that string correction cannot see](when-the-typo-is-a-real-word/) — a typo that is itself a valid catalog
term never fires edit-distance correction, so the evidence has to come
from the click log.
