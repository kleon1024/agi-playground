---
status: verified
level: applied
base: scratch
label: When the null is elevated
verified: 2026-08-06
---

# The honest null, elevated to a verdict

**Question:** [mission 06's full-chain report](../) returned MET — as an
honest null result. A verdict of MET for a mission whose policies lost to
their baselines sounds like a contradiction until you read the acceptance
bar's second disjunct. This chapter reads that structure.

**Before this:** [mission 06's full-chain report](../) and the
not-met-verdict chapter.

## The structure, read

The run ([record](runs/2026-08-06-null-verdict.md)) tabulates the two
environments:

| environment | evidence |
|---|---|
| grid-world | greedy decode loses decisively to both baselines |
| MiniGrid | honest null — 100% degenerate steps, 0% eval success |

Acceptance bar: beats both baselines beyond spread, **OR** reports an
honest null result with mission 01's own rigor.

## Two readings

**The disjunct makes a rigorous negative a deliverable.** The grid-world
arm alone reads NOT MET (decisive losses), and the report leaves that
verdict standing. The full-chain verdict evaluates the bar's second
disjunct: MiniGrid's null — 100% degenerate steps, 0% eval success,
reported with the mission's rigor — is a real result, which is what
MET-as-null means. The mission proved a boundary (when GRPO's cold start is
total) rather than claiming an outcome it did not reach.

**NOT MET would misread the acceptance bar.** The bar explicitly allows
the null when it is reported with rigor, so calling the mission NOT MET
because the policies lost would be grading it against the first disjunct
only. The two-environment null — the cold-start boundary reproduced on the
grid-world's near-miss and MiniGrid's total — is the mission's actual
deliverable, and the verdict names it.

## Evidence boundary

The recorded full-chain report and its environment verdicts; no re-training.
It reads the verdict structure; it does not re-derive the baselines or the
null evidence, and it does not claim the null "counts as winning" — it
claims the null is what the acceptance bar asked for.

## Check your mental model

Answer each before opening it.

**1. How can a mission whose policies lost to their baselines be MET?**

<details>
<summary>Answer</summary>

Because the acceptance bar has two disjuncts: beat the baselines beyond
spread, OR report an honest null with mission 01's own rigor. The mission
did not meet the first (its greedy decode lost decisively), but it did meet
the second — the MiniGrid null (100% degenerate steps, 0% eval success)
was reported with the full evidence discipline. The verdict is not a win;
it is a rigorous negative, which the bar explicitly accepts as a
deliverable.

</details>

**2. Why does the report keep the grid-world NOT MET verdict and still
report MET overall?**

<details>
<summary>Answer</summary>

Because the two verdicts answer different questions. The grid-world arm's
NOT MET is its own honest result — the policy lost there, and that is not
erased. The full-chain MET evaluates the mission against the complete
acceptance bar, where the honest null across two environments satisfies the
second disjunct. Keeping both verdicts visible is the report's honesty: the
null is elevated without pretending the losses were wins.

</details>

## Next

Back to [mission 06's full-chain report](../), or to
[the cold-start chapter](../../04-minigrid/when-the-cold-start-is-total/)
where the null's mechanism is measured.
