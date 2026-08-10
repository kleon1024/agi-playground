# Run — the prompt-order audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/llm_rank.py --emit-log /tmp/rank-order-envelope.json` then `uv run python prod/rank_order_audit.py /tmp/rank-order-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 31 ranks with an LLM that sees the whole list as context. The
failure mode this audit exists for is prompt-order sensitivity: the
same candidate set can rank differently just because the prompt wrote
the candidates in a different order. The audit ranks each query's
forward and reverse prompt answers and stratifies the displacement by
head and tail — the case-finding that shows which queries the prompt
writing actually decides.

## Output

```
prompt-order audit over the 20-query log:
  aggregate mean displacement: 0.520

  stratum  queries  swing  mean displacement
  head     10       0      0.000
  tail     10       10     1.040

verdict: PROMPT ORDER SWINGS THE REORDER IN THE TAIL --
head rankings are stable (0/10 queries swing, mean
displacement 0.00) while tail
rankings change with the written order (10/10 queries swing, mean displacement 1.04). The tail judgment
calls are not a stable ranking -- they are a function of how
the candidates were written into the prompt. The check is
forward-versus-reverse agreement on the tail before the LLM
reorder ships; where it swings, keep the pointwise order
(Qin et al. 2023) or sample the LLM more than once and
aggregate.
```

## Notes

- The audit cohort is a 20-query log with a forward and a reversed
  prompt ranking per query. Head queries reorder stably: 0/10 swing,
  mean absolute position displacement 0.000. Tail queries swing with
  the written order: 10/10 swing, mean displacement 1.040.
- The aggregate displacement of 0.520 is a head artifact: every unit
  of prompt-order sensitivity lives in the tail, where the preference
  is a judgment call and the prompt writing becomes part of the
  decision.
- Sun et al., "Is ChatGPT Good at Search? Evaluating Large Language
  Models as Re-Ranking Agents", arXiv:2304.09542, 2023, documents the
  reordering behavior of LLM rankers across query difficulty; Qin et
  al., "LLMs are Effective Text Rankers with Pairwise Ranking
  Prompting", arXiv:2306.17563, shows how the way candidates are
  presented (single vs pairwise, order within the pair) changes the
  LLM's verdict. The decision that follows: gate the LLM reorder on
  forward-versus-reverse tail agreement, and where it swings keep the
  pointwise order or sample-and-aggregate.
