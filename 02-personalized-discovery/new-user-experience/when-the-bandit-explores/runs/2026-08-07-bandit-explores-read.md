# Run — when the bandit explores, executed on the exploration-tax read

**Date:** 2026-08-07
**Command:** `uv run python core/bandit_explores.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 51's detour: exploration is the other lever for the first page,
and on the new-user runway it is a tax, not a gift. This run plays
greedy, epsilon-greedy at 10% and 30%, and Thompson sampling over the
same 20-round runway from a popularity-initialized estimate, and
measures the NDCG@10 each policy earns per round on average.

## Output

```
bandit explores, read (NDCG@10 over the 20-round runway):
  policy          round 1  round 5 round 20 runway avg
  popularity        0.122    0.122    0.122      0.122
  greedy            0.122    0.878    0.878      0.817
  epsilon 10%       0.122    0.878    0.878      0.795
  epsilon 30%       0.122    0.878    0.878      0.728
  Thompson          0.122    0.694    0.878      0.731

reading: everyone who learns ends at the same 0.878 - the
difference is what the runway cost to get there. Greedy from
a popularity-initialized estimate explores implicitly through
its ties and pays nothing; a fixed 10% exploration budget
costs 0.022 of runway average; 30% costs
0.090. Thompson spends exploration only
where the posterior is uncertain, but even it pays
0.087 on a runway this short.
Exploration is a tax during the new-user runway; on a short
horizon it is mostly cost, which is why the prior - the
stage's other lever - moves the first page more than the
exploration budget does.
```

## Notes

- All learning policies end at the same 0.878 NDCG; the difference is
  the runway average each one earned while learning. Greedy from the
  popularity prior pays nothing (0.817); a fixed 10% budget costs 0.022
  (0.795), 30% costs 0.090 (0.728), and Thompson pays 0.087 (0.731).
- The production tell is a new-user cohort whose early-session relevance
  trails the same cohort a week later: the cohort is paying the
  exploration tax. On a short horizon the prior moves the first page
  more than the exploration budget does (Thompson, 1933, for the
  posterior-sampling original).
