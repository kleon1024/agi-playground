# Run — when the output cannot be parsed, executed on the parse-failure read

**Date:** 2026-08-07
**Command:** `uv run python core/output_parse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 31's LLM ranker answers in text. This run parses a 12-response
cohort two ways — the naive parse that accepts the text and the
validate-and-resample path that structurally checks it — and reads the
cost of the repair.

## Output

```
llm ranking output, read:
  cohort: 12 responses
  parse clean:    7
  invalid:        5 (duplicate id 2, missing id 2, extra token 1)
  naive parse:    5 of 12 reorders
                  serve a damaged list (5 docs dropped, 1 phantom id served)
  validate + resample: repaired 5 of 5 invalid
                  responses; 5 docs recovered, 1 phantom removed; cost: 5 extra
                  inference calls (one per invalid response)

reading: the text answer is not a list. A parser that accepts
the text silently ships a shorter or wider list -- dropped docs
and a phantom id. The structural check catches the three shapes,
and the resample repairs them at the cost of one extra inference
round per invalid response.
```

## Notes

- The cohort contains 7 clean responses and 5 invalid ones: two
  duplicate-ID answers, two missing-ID answers, and one answer carrying
  an ID outside the candidate set.
- The naive parse serves a damaged list on 5 of 12 responses: five
  documents dropped and one phantom ID served. A position-count check
  would not catch the duplicate-ID cases, because the list length
  still reads five.
- The validate-and-resample path repairs all 5 invalid responses —
  keeping the valid prefix and appending the missing documents in
  pointwise order — and its measured cost is 5 extra inference calls,
  one per invalid response.
