---
status: verified
level: applied
base: scratch
label: When the case is hiding
verified: 2026-08-08
---

# How do you find the failure cases the report demands?

**Question:** [stage 09's report](../) treats failure cases as required
evidence — a report with none has either not looked or is not telling you.
This chapter is the looking: the workflow that turns an aggregate pass into
concrete, measured cases. The executed run passes the aggregate and shows
the cases hiding inside the slices.

**Before this:** [stage 09's report](../), which requires seed-level
metrics, guardrails, and a failure catalogue before any success claim.

## The case-finding workflow, executed

The run ([record](runs/2026-08-08-case-finding.md)) simulates 15,000 users
through a recommendation loop with two defects baked in, then applies the
workflow. Step one is the aggregate, and it passes: candidate nDCG@10 0.326
against 0.082 for popularity and 0.112 for item-item CF. A report written
from this row alone would claim a win and attach no cases.

Step two slices by the cohort — interaction count:

| interactions | users | candidate | CF | popularity | gap to 21+ |
|---|---:|---:|---:|---:|---:|
| 0-4 | 3,181 | 0.086 | 0.096 | 0.086 | -0.332 |
| 5 | 1,184 | 0.301 | 0.121 | 0.079 | -0.117 |
| 6-10 | 3,639 | 0.371 | 0.112 | 0.080 | -0.047 |
| 11-20 | 4,003 | 0.417 | 0.118 | 0.082 | -0.001 |
| 21+ | 2,993 | 0.418 | 0.119 | 0.082 | 0.000 |

The boundary group sits exactly at five interactions, and the 0-4 bucket
is pure popularity. Step three slices by the item side the system can
serve — the preferred category's recall-pool cap:

| preferred category | users | candidate | CF | popularity | pool cap |
|---|---:|---:|---:|---:|---:|
| head | 8,927 | 0.424 | 0.166 | 0.124 | 200 |
| mid | 4,503 | 0.217 | 0.035 | 0.021 | 60 |
| tail | 1,570 | 0.083 | 0.025 | 0.022 | 10 |

Step four drills into the worst 50 rows. Tail users are 10% of the
population and 28% of the worst 50 (14 of 50); the interaction mix is
0-4: 24, 5: 6, 6-10: 10, 11-20: 5, 21+: 5. User 58 is the drill's sharpest
row: 16 interactions, tail preference, personalization landed — and the
candidate still scores 0.000 while popularity scores 0.095.

Step five verifies the mechanisms, not the anecdotes: personalization lands
65% of the time at exactly 5 interactions, 82% at 6-10, 95% at 11-20; the
tail recall pool holds 300 items and is capped at 10 — exactly one slate,
so the ranker has nothing to reorder.

## The reading

**The aggregate passing is the moment the report is most in danger.** A
report written from the headline row would be a win with an empty case
list — it satisfies "failure cases are required evidence" in the way that
means no one looked. The two trailing slices are the answer to "how do you
find the case": slice by the cohort that defines who personalization is
supposed to help, and by the capacity that can starve an item side before
the ranker ever sees it. Both slices trail for a mechanism reason, and both
fixes are named in the case files, which is what makes a case actionable
instead of an observation.

**A slice is a hypothesis until the mechanism count confirms it.** The
worst-50 drill alone would produce a plausible-sounding story about
interaction counts — but the mechanism check is what pins it: the 5-bucket
gap is a 65%-versus-95% landing-rate difference, and the tail gap is a
10-item pool. Case-finding in production is this same loop against logged
rows: slice on declared dimensions, drill to rows, check the mechanism
count, and only then write the case with its fix target. Automated tools
mechanize the slice search (Slice Finder, Chung et al., ICDE 2019) and the
drill (What-If Tool, Wexler et al., IEEE VIS 2019), but they do not remove
the hypothesis check.

## The fix and its trade

The fix is a workflow, not a model change: every report slices the
aggregate by cohort and by item-side capacity, drills the trailing slices
to rows, verifies the mechanism count, and attaches each case with a named
fix target. The two cases this run produces carry their targets. The
eligibility boundary: personalization lands 65% of the time at exactly
five interactions, so the team either moves the boundary (do not claim
personalization before the landing rate is trustworthy) or improves the
cluster estimate that is noisy at five. The tail recall pool: a 10-item cap
is one slate, so the recall owner widens the rare-category pool or
backfills from cluster-neighbor items in other categories.

The trade, named: slicing is a multiple-comparisons machine — every
dimension is another chance to find a "failure" that is seed noise. The
mechanism verification is the counterweight: a slice becomes a case only
when its mechanism count confirms it, and the guardrail slices are declared
before results so the case list cannot grow to fit a narrative. The hidden
cost is plumbing: drilling requires per-row logging with the cohort labels
attached, and slice tables multiply the analysis surface every evaluation
must pay for.

## Who owns the loop

- **The evaluation team** owns the slice tables and the drill — every
  report attaches its case files, and a report whose cases could have been
  written from the aggregate alone has not looked.
- **The data pipeline team** owns the cohort definitions and the per-row
  logging that makes drilling possible — a slice you cannot drill to rows
  is a rumor.
- **The recall owner** owns the category-pool caps and the item-side
  capacity numbers the tail case names.
- **The product owner** owns the eligibility boundary — when
  personalization starts is a promise about whom the system helps, not a
  free knob.

## Evidence boundary

The run is a deterministic synthetic simulation (seeded stdlib RNG,
15,000 users, two defects with declared probabilities) that demonstrates
the workflow; it is illustrative and not a mission result. Real
case-finding runs on logged production rows and must record the logging
cutoff, cohort definition, and revision next to the slices. The tools
cited (Slice Finder, ICDE 2019; What-If Tool, IEEE VIS 2019) were verified
on 2026-08-08; their claims are the authors', and this chapter leans on
them only as mechanizations of the slice-and-drill loop executed here.

## Check your mental model

Answer each before opening it.

**1. The aggregate passed. Why is the report still incomplete?**

<details>
<summary>Answer</summary>

Because the report demands failure cases as evidence, and the aggregate
says nothing about whom the system fails. The headline 0.326 is carried by
the head and trusted cohorts; the slices show 3,181 cold users at 0.086
and 1,570 tail users at 0.083. A win without a case list is a claim that
no one checked for the people the system misses.

</details>

**2. Why does the tail appear in the worst-50 drill at more than its
population share?**

<details>
<summary>Answer</summary>

Because small pools concentrate the worst rows. Tail users are 10% of the
population and 28% of the worst 50, and user 58 shows the mechanism: the
ranker is right about taste, but a 10-item pool is exactly one slate — the
candidate scores 0.000 while popularity scores 0.095. When the pool can
hold one list, the ranker has nothing to reorder, and every such user is a
potential bottom row.

</details>

**3. What turns a slice into a case?**

<details>
<summary>Answer</summary>

A mechanism count that confirms it and a named fix target. "0.301 at five
interactions" is a number; the case is "personalization lands 65% of the
time at exactly five interactions versus 95% at 11-20, so the eligibility
boundary is the fix target." A slice without a confirmed mechanism is seed
noise; a case without a fix target is an anecdote.

</details>

## Next

Back to [stage 09's report](../), where this case list is one of the
required inputs, or to the sibling that shows the veto a case can trigger —
[when the guardrail vetoes](../when-the-guardrail-vetoes/) — and the one
that checks whether a found gap is real — [the variance that
decides](../the-variance-that-decides/).
