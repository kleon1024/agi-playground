# Run — the annealed mix as a two-skill seesaw, measured

**Date:** 2026-08-08
**Command:** `uv run python core/mix_seesaw.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

The mid-training mix decision is a multi-objective trade wearing the
clothes of a pipeline detail. This run builds the seesaw explicitly: an
anneal window of 20,000 docs, a declared agentic share s from 0 to 10
percent, and two skill axes the window teaches. Agentic skill saturates,
`A(s) = 1 - exp(-40s)` — the first points of share buy most of the
capability. General skill loses with a recency multiplier,
`G(s) = 1 - 1.6s` — displaced general tokens in the final window hurt
more than uniform displacement, because annealed tokens dominate the
final checkpoint. The audit sweeps the share, prints the two eval curves
and their marginal trade, and asks whether a blended aggregate can see
the seesaw at all.

## Output

```
anneal window: 20,000 docs; sweep s = 0..10% agentic share
agentic skill A(s) = 1 - exp(-40s); general skill G(s) = 1 - 1.6s (annealed displacement weighs more than uniform)
guardrail: general eval >= baseline - 10%

share   agentic  general  blended  general-delta   verdict
 0.00     0.000    1.000    0.500    +0.000   within guardrail
 0.01     0.330    0.984    0.657    -0.016   within guardrail
 0.02     0.551    0.968    0.759    -0.032   within guardrail
 0.03     0.699    0.952    0.825    -0.048   within guardrail
 0.05     0.865    0.920    0.892    -0.080   within guardrail
 0.08     0.959    0.872    0.916    -0.128   GUARDRAIL BREACH
 0.10     0.982    0.840    0.911    -0.160   GUARDRAIL BREACH

marginal trade, per point of share (share -> next share):
  from     to   dA/pt   dG/pt   agentic still pays?
   0.00   0.01   32.97   -1.60   yes
   0.01   0.02   22.10   -1.60   yes
   0.02   0.03   14.81   -1.60   yes
   0.03   0.05    8.29   -1.60   yes
   0.05   0.08    3.15   -1.60   yes
   0.08   0.10    1.12   -1.60   no -- the trade has flipped

verdict: the general slice breaches its guardrail at s = 0.08, before the
agentic eval saturates (agentic 0.959 of a saturating curve). The marginal
trade flips between s = 0.08 and s = 0.10: each point of agentic share
buys 1.12 of agentic eval against a 1.60 general-eval cost, so past the
knee the trade no longer pays. The blended number rises through the
breach (0.892 at s = 0.05 to 0.916 at s = 0.08), so an aggregate-only
read rewards exactly the move that breaks the contract -- the slice read
is the case-finding step.
```

## Reading the output

- **The guardrail binds before the saturation.** The agentic eval is 0.865
  at s = 0.05 and 0.959 at s = 0.08, but the general slice falls below its
  `baseline - 10%` guardrail at s = 0.08. The safe band is 5-8 percent;
  10 percent buys only 0.023 more agentic eval for a 0.160 general-eval
  loss.
- **The marginal flip marks the knee.** Agentic gain per point of share
  falls from 32.97 at the start to 3.15 in the 5-8% band to 1.12 at
  8-10%, while the general cost per point stays flat at 1.60. The trade
  stops paying between 8 and 10 percent — the top of the reported
  single-digit practice band.
- **The aggregate hides the breach.** The blended number rises from 0.892
  at s = 0.05 to 0.916 at s = 0.08 — the breach point — so a team watching
  only the blended eval is rewarded for exactly the move that breaks the
  contract. The slice read (agentic vs general) is the case-finding step.
- **The zero-share anchor matches the stage's own run.** At s = 0 the
  agentic eval is 0, which is the same story the agent chapter's measured
  0/6 run tells about a checkpoint that never saw an agentic-formatted
  example.

## Evidence boundary

This is a mechanism demo, not a trained model: the two curves are declared
formulas (`A(s) = 1 - exp(-40s)`, `G(s) = 1 - 1.6s`) chosen to make the
seesaw legible at toy scale, and the exact rates do not transfer to a real
corpus. What transfers is the shape of the failure: a slice that saturates
while another slice pays a flat, recency-weighted cost, and an aggregate
that cannot see the falling slice. The real training-scale numbers this
chapter's README reasons about are cited, dated external results: Agentic
CPT's 300B-token budget (arXiv:2509.13310, 2025), GLM-5's mid-training at
roughly 5% of the pretraining budget (Kili Technology, 2026), and the
mixing-effect evidence of DCLM (Li et al., arXiv:2406.11794, Jun 2024),
FineWeb-Edu (Penedo et al., arXiv:2406.17557, Jun 2024), and DoReMi (Xie
et al., arXiv:2305.13029, May 2023).
