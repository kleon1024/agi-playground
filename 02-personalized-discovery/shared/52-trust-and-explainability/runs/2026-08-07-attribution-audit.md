# Run — the explanation-surface audit over the emitted surface rows

**Commands:** `uv run python core/attribution.py --emit-log /tmp/attribution-envelope.json`;
`uv run python prod/attribution_audit.py /tmp/attribution-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 52's read shows the attribution that builds trust is the one
whose largest term the user can check. This run is the case-finding half
of the stage: explanation coverage is healthy in the aggregate, and the
surface that leads with an uncheckable headline is invisible until you
stratify by surface. The core script emits per-surface rows; the
production audit compares each surface's headline-verifiable share
against the aggregate, the way a trust or UX team reads explanation
telemetry.

## Output

```
explanation-surface audit (headline verifiability by surface):
  surface             traffic explained headline verifiable  vs aggregate
  home feed               45%       85%                72%          +10%
  search results          20%       90%                85%          +23%
  similar-users recs      25%       80%                30%          -32%
  email digest            10%       95%                55%           -7%
  aggregate              100%       86%                62%

verdict: UNVERIFIABLE HEADLINE -- the similar-users recs surface
leads with a claim the user cannot check on 70% of its items,
against a 62% aggregate headline-verifiable share.
The aggregate hides it because home feed and search are
verifiable-heavy; on the surface that leans on 'similar users
bought', the largest term is a black box the user has no record
to check. Surface the verifiable terms first on that surface or
drop the black-box headline before the trust is spent.
```

## Notes

- The similar-users recs surface leads with a claim the user cannot
  check on 70% of its items, 32 points below the aggregate
  headline-verifiable share of 62%.
- The aggregate hides it because home feed and search are
  verifiable-heavy: the surface that leans on 'similar users bought'
  spends trust on a black-box headline the user has no record to check.
  The audit's message is the stage's: surface the verifiable terms first
  on that surface or drop the black-box headline before the trust is
  spent. Explainable-recommendation surveys (Zhang & Chen,
  "Explainable Recommendation: A Survey and New Perspectives",
  Foundations and Trends in Information Retrieval 2020) make
  verifiability a first-class explanation-quality criterion.
