# Run — trust and explainability, executed on the contribution read

**Date:** 2026-08-07
**Commands:** `uv run python core/attribution.py --emit-log /tmp/attribution-envelope.json`;
`uv run python prod/attribution_audit.py /tmp/attribution-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 52 introduces explanation quality. This run attributes one shown
item's score to its features and marks which claims the user can verify,
then emits the per-surface explanation rows the production audit
stratifies by surface.

## Output

```
trust and explainability, read (contributions to the score):
  price                    value 3.0  x weight -0.008 = -0.0240 (penalty, verifiable)
  category affinity        value 0.2  x weight +0.040 = +0.0080 (19% of score, verifiable)
  similar users bought     value 0.9  x weight +0.022 = +0.0198 (47% of score, unverifiable)
  you viewed this category value 0.4  x weight +0.035 = +0.0140 (33% of score, verifiable)

reading: the largest contribution is 'similar users bought', which the
user cannot check - no record of similar users exists on their
side. The verifiable claims ('you viewed this category',
'category affinity') are smaller. Trust is built on explanations
the user can falsify, not on the term with the largest coefficient.

surface view (explanation coverage by surface):
  surface             traffic explained headline verifiable
  home feed               45%       85%                72%
  search results          20%       90%                85%
  similar-users recs      25%       80%                30%
  email digest            10%       95%                55%
  aggregate              100%       86%                62%

  reading: 86% of shown items carry an explanation and the
  aggregate headline is 62% verifiable, but the similar-users
  recs surface leads with an uncheckable claim on 70% of its
  items. Stratify by surface before declaring the explanation
  policy healthy.
```

## Notes

- The largest contribution (47%) is 'similar users bought', which the user cannot check; the verifiable claims are smaller.
- Trust is built on explanations the user can falsify, not on the term with the largest coefficient.
- The surface view is the case-finding half of the stage: 86% of shown
  items carry an explanation and the aggregate headline is 62%
  verifiable, but the similar-users recs surface leads with an
  uncheckable claim on 70% of its items. The audit reads the emitted
  envelope and returns the UNVERIFIABLE HEADLINE verdict; see the audit
  record.
