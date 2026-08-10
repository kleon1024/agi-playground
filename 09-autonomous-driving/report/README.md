---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# What did this prove, and what does it deliberately not prove?

**Goal:** assemble the topic's runs into a single table and verdicts against
the declared acceptance criteria in [`mission.yaml`](../mission.yaml) —
reading only the runs/ JSON files, never new numbers.

**Why this stage exists.** A topic with seven measured stages and no report
is seven claims without a conclusion. The report is where the evidence gets
one interpretation, where NOT MET verdicts are stated instead of hidden, and
where the boundary of what the simulator cannot claim is written down next
to the numbers. It is also the artifact a learner can take to an interview
and defend: every figure in it traces to a run.

## What we measured

```bash
cd 09-autonomous-driving/06-report/core
python report.py
```

Closed-loop completion rate, 50 scenarios per cell:

| Cell | Completion |
|---|---|
| Rule baseline (in-distribution) | 0.28 |
| Expert (in-distribution) | 0.92 |
| Cloned (in-distribution) | 0.28 |
| Expert (hard) | 0.78 |
| Cloned (hard) | 0.04 |

Verdicts:

| Criterion | Verdict |
|---|---|
| Cloned beats rule baseline | NOT MET — 0.28 vs 0.28 |
| Imitation-vs-loop gap reported | MET — 0.77 accuracy vs 0.28 completion |
| Every stage has a runs/ entry | MET |
| Hard boundary reported as a finding | MET |
| does_not_prove boundary stated | MET |

## The finding, in one sentence

A policy trained purely on expert demonstrations matched the expert on 77%
of held-out frames and then drove exactly like a controller with no
avoidance logic — imitation accuracy did not transfer to the loop, and the
gap widened to total collapse on out-of-distribution scenarios.

## The fix and its trade

The fix is a report that reads only the runs/ JSON files and renders
verdicts against the declared acceptance criteria — the five-row completion
table (floor 0.28, expert 0.92, clone 0.28 in-distribution; expert 0.78,
clone 0.04 hard) beside the four-MET/one-NOT-MET verdict list. The trade is
the itemized structure: it separates the discipline from the outcome, so
the NOT MET headline (clone 0.28 vs floor 0.28) stands plainly while the
imitation-vs-loop gap (0.77 accuracy vs 0.28 completion) and the stated
does_not_prove boundary read as evidence of a well-run mission, not as
consolation. The fix buys one interpretation of seven stages — the
artifact a learner can defend in an interview, where every figure traces
to a run — at the cost of a negative headline the acceptance criteria
demand be stated rather than hidden.

## Who owns this loop

- **The report owner** owns the reading-only verdict contract: the report
  never computes a new number, it tabulates what runs/ already recorded.
- **The stage owners** own the runs/ records each verdict reads; a verdict
  without a traceable run is a defect in the stage, not the report.
- **The mission owner** owns the does_not_prove boundary written next to
  the numbers and the acceptance criteria the verdicts are judged against.

## Evidence boundary

This topic does not make any claim about driving on real roads, real
vehicles, or real sensors. The simulator is 2-D, synthetic, and
deterministic; the render carries almost no obstacle signal (stage 01); and
the generalization boundary in stage 05 is a boundary of this simulator's
generator. The method-level finding — open-loop imitation accuracy can
overstate in-loop competence — is what carries outside this repository.
Numbers trace to
[`runs/2026-08-07-report.json`](runs/2026-08-07-report.json).

## Next

The reading-only verdicts are stress-tested in
[when the verdict survives resampling](when-the-verdict-survives-resampling/):
every cell re-simulated per seed, a paired 2,000-draw bootstrap, and the
finding that the two 0.28 cells are the same 14 scenarios.
