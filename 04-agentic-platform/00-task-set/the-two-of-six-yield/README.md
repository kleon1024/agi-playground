---
status: verified
level: applied
base: scratch
label: The two-of-six yield
verified: 2026-08-06
---

# The yield is the finding

**Question:** [stage 00's task set](../) mines bug-fix tasks from git
history. This chapter reads the recorded mining runs and asks how many
candidates actually become tasks.

**Before this:** [stage 00's task set](../) and its recorded mining runs.

## The yields, read

The run ([record](runs/2026-08-06-yield-read.md)) reads both records:

| source | commits | candidates | survived |
|---|---:|---:|---:|
| private (this repository) | 100 | 4 | 2 |
| public (more-itertools) | 2,423 | 6 | 2 |

## Two readings

**Most commits that look like fixes do not survive verification.** Both
histories produce the same low yield: 2 of 4 and 2 of 6 candidates pass
fail-at-base/pass-at-gold. The survivors are the tasks whose gold commit
actually fixes the failing test and nothing else; the rest are refactors,
test-only changes, or fixes that did not reproduce. The yield is the
finding, not a shortcoming of the mining.

**The verification step, not the mining, is what makes a task real.** The
candidates are cheap to find; the full test run at base and gold commits
(4:45 for six public candidates) is what separates a real task from a
commit that merely touched tests. A task set built by mining alone, without
verification, would be contaminated with non-tasks — which is why the
admission rule, not the search, is the stage's core.

## The fix and its trade

The fix is the verification gate between candidates and tasks:
fail-at-base/pass-at-gold, run for real at both commits. The trade is
measured in the yield table: 2 of 4 and 2 of 6 survive, because most
fix-looking commits are refactors, test-only changes, or fixes that do not
reproduce. Verification costs wall-clock (4:45 for six public candidates)
and rejects most of history on purpose — the strictness is what keeps the
resolve metric meaningful. The alternative, mining without verification,
produces tasks whose gold patch does not fix a failing test, and every
number measured on them inherits the lie.

## Who owns the loop

- **The benchmark owner** owns the admission rule and the verify runs —
  the same rule, applied to both histories, is what makes the two sets
  comparable.
- **The routing owner** inherits the yield: a 2-of-6 survival means the
  final task set is small and selected, and resolve rates must be read
  against that, not as general capability.
- **The report owner** owns the interpretation that a low yield is the
  finding, not a shortcoming — the funnel's shape is the benchmark's
  quality claim.

## Evidence boundary

The recorded mining runs (one 100-commit history, one 2,423-commit history,
one commit pin each). It reads those artifacts; it does not re-mine and the
yields characterize these two repositories, not task mining in general.

## Check your mental model

Answer each before opening it.

**1. Why does the public set (2,423 commits) yield only 2 tasks?**

<details>
<summary>Answer</summary>

Because yield is about survival through verification, not about history
size. A commit must fail at base, pass at gold, and touch no unrelated
files to become a task — most fix-looking commits fail one of those checks.
The 2,423-commit history produces 6 candidates and 2 survivors; the size
of the history does not change how strict the admission rule is.

</details>

**2. What would a task set without verification contain?**

<details>
<summary>Answer</summary>

Candidates — commits that look like fixes but were never checked. Without
fail-at-base/pass-at-gold, a refactor or a test-only commit becomes a
"task" whose gold patch does not actually fix a failing test, and the
mission's resolve metric would measure the wrong thing. The verification
run is what converts candidates into tasks, and the low yield is its
honeypot.

</details>

## Next

Back to [stage 00](../), or to
[what the mined task set actually contains](../what-the-task-set-contains/)
which reads the same stage's manifest.
