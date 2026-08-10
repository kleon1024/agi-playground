# Run — the cost-attribution audit over the emitted scale rows

**Commands:** `uv run python core/cost.py --emit-log /tmp/cost-envelope.json`;
`uv run python prod/cost_audit.py /tmp/cost-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 50's read prices the cascade at one catalogue size. This run is
the case-finding half of the stage: the stage that owns the query
budget moves with the catalogue, and the audit attributes the budget per
stage per scale the way a cost team reads sampled per-stage spans.

## Output

```
cost-attribution audit (units per stage per catalogue):
   catalogue recall (ann)    pre-rank   fine-rank      mixing    total
         10M        1.00        1.00        1.00        1.00     4.00
        100M        2.51        1.00        1.00        1.00     5.51
          1B        6.31        1.00        1.00        1.00     9.31

share of the query budget by stage:
   catalogue recall (ann)    pre-rank   fine-rank      mixing
         10M         25%         25%         25%         25%
        100M         46%         18%         18%         18%
          1B         68%         11%         11%         11%

verdict: RECALL DOMINANT -- recall owns 68% of the
query budget at the 1B catalogue, against 25% at 10M. The
flat 1.0-each design holds only at the declared size; as the
catalogue grows, the ANN index's candidate set is what the
budget follows. Optimize recall (index quality, candidate
budget, embedding size) before touching fine-rank.
```

## Notes

- Recall candidates scale sublinearly with the catalogue (100k at 10M
  to 631k at 1B under a catalogue^0.4 rule), so recall's share of the
  query budget grows from 25% to 68% while pre-rank, fine-rank, and
  mixing hold fixed budgets.
- The audit's message is the stage's: attribution is how you find which
  stage owns the budget at your scale; the levers that move it are
  cheaper per-candidate models (Han et al., "Deep Compression", ICLR
  2016) and candidate-budget cuts.
