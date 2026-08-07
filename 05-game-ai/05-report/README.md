---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Full-chain report
---

# Does mission 06's full chain, stages 00-04, meet its own acceptance bar?

**Question:** `mission.yaml`'s acceptance bar, written before stage 00
existed, allows two outcomes: beat both baselines by more than run-to-run
spread, or report an honest null result with the rigor mission 01's 04-rl
applied to its own zero-gradient arithmetic run. Stage 02 already answered
this for stages 00-01 alone (NOT MET, greedy decode collapses below both
baselines). This stage answers it for the mission's full, later-approved
scope: stages 00-01, 03 (the collapse-fix sweep), and 04 (the MiniGrid
extension), together.

**The artifact this stage produces** is a single script that reads every
upstream stage's own `runs/` JSON directly and prints one verdict --
never a hand-copied number, never a softened paraphrase.

**Before this:** [stage 04](../04-minigrid/), whose cold-start null result
on MiniGrid is the piece that completes the honest-null-result reading of
this mission's full chain.

## The full chain, briefly

| Stage | What it found |
|---|---|
| 00-01 | GRPO takes real gradient steps (199-200/200 per seed) on a fully-observed 5x5 grid-world, but greedy decode collapses to one fixed, board-independent action per seed -- decisively below both baselines |
| 03 | Neither of the two most directly-motivated fixes (smaller rollout groups, an entropy bonus) repairs the collapse; smaller groups make every measured number worse |
| 04 | Moving to MiniGrid (real partial observability, real episode termination), the cold-start policy's success rate is so far below its own random baseline that every group across 3 seeds draws zero reward variance -- zero gradient steps taken, ever |

Run `uv run python core/report.py` for the full numeric verdict, read
directly from every upstream `runs/` file:
[`runs/2026-08-01-full-chain-report.md`](runs/2026-08-01-full-chain-report.md).

"Decisively below both baselines" is a phrase carrying a lot of weight. Put
every arm on one axis and switch environments to see how far below, and against
how much seed-to-seed movement:

<!-- interactive: GrpoNullResult -->

## Verdict

**MET, as an honest null result extended across two environments and one
fix attempt.** Stage 01's collapse is not an unexplained shortfall -- stage
03 shows it resists the two most obvious training-signal fixes, one of
which actively makes it worse. Stage 04's cold start is not a broken
environment -- a simple scripted heuristic solves the same MiniGrid room
100% of the time, and the random baseline (0.4% success) mechanistically
explains why every rollout group drew zero variance. Per `mission.yaml`'s
own guardrail, this is reported plainly as a null result, never
retroactively rescaled or warm-started to manufacture a positive number.

## What this mission, taken as a whole, does not prove

Per `mission.yaml`'s `does_not_prove`: nothing here generalizes to pixel
observations, real-time play, multi-agent or competitive play, or
environments without early termination. A result on a 5x5 grid-world or
MiniGrid-Empty-6x6 says nothing about a harder game, and none of this
depends on mission 05's vision work, since MiniGrid's observation is a
compact symbolic grid, not pixels.

**Next:** this closes mission 06's currently-approved scope. A future
stage could test whether a warm start, a shaped reward, or a longer run
produces a non-degenerate MiniGrid training step -- none of which were
tried here.

A detour from here: [the honest null, elevated to a
verdict](when-the-null-is-elevated/) — the acceptance bar's second
disjunct read: a rigorous negative is a deliverable, NOT MET would misread
the bar, and the two-environment null is the mission's actual result.

Another detour: [the null that repeated is the finding](the-two-environment-null/) — the recorded report read: the acceptance bar's second disjunct turns two failures into one pattern, and MET-as-null is the correct reading over NOT MET.
