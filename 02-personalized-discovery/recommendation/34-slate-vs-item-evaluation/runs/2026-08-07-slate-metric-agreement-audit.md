# Run — the slate metric-agreement audit over the comparison log

**Date:** 2026-08-07
**Command:** `uv run python core/slate_eval.py --emit-log /tmp/slate-metric-envelope.json` then `uv run python prod/slate_metric_audit.py /tmp/slate-metric-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 34 evaluates slates, not items. The failure mode this audit
exists for is metric disagreement: the item-level metric (score sum)
and the slate-level metric (diversity-adjusted value) rank the same
page differently, so an item-only report picks the wrong winner
exactly where the slate is near-tied. The audit stratifies a
20-comparison log by head and tail and reports where the two metrics
pick different winners.

## Output

```
slate metric-agreement audit over the 20-comparison log:
  stratum  comparisons  item-sum wins a  slate-value wins a  agree
  head     10           10                10                 10/10
  tail     10           10                0                  0/10

verdict: THE METRICS AGREE ON HEAD SLATES AND FLIP ON TAIL
SLATES -- on head comparisons item-sum and slate-value pick
the same winner (10/10). On tail comparisons every winner
flips (0/10): the higher item-score sum loses on slate
value once diversity counts. An item-level report is right
where the decision is easy and wrong where it matters.
Report the winner per metric and declare which metric the
product optimizes before tuning the ranker (Ie et al. 2019;
Craswell et al. 2008).
```

## Notes

- The audit cohort is a 20-comparison log, each comparison two slates
  scored by item-score sum and diversity-adjusted slate value. Head
  comparisons agree on the winner (10/10); tail comparisons flip on
  every one (0/10): the higher item-score sum loses on slate value
  once diversity counts.
- The flip is concentrated in the tail, so a report that only averages
  item scores is right where the decision is easy and wrong where it
  matters — the near-tied slate is exactly where the evaluation has to
  see the page.
- Ie et al., "SlateQ: A Tractable Decomposition for Reinforcement
  Learning with Recommendation Sets", IJCAI 2019, pp. 2592-2599, is
  the slate-value reference — the page-level value is not the sum of
  item-level values. Craswell et al., "An Experimental Comparison of
  Click Position-Bias Models", WSDM 2008, pp. 87-94, is the
  position-bias reference that explains why raw click feedback cannot
  stand in for slate value.
