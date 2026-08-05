# Run — the no-harness failure surface, second cut

**Date:** 2026-08-06
**Command:** `uv run python core/no_harness_failures.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane; the inputs were the mission's own recorded model
attempts).

## Purpose

Stage 04's recorded taxonomy printed the category table. This run reads the
same two logs and makes a complementary cut — not the category each attempt
fell into, but what the failures cost: how many blind calls produced a patch
that could not even be applied, the time and money the failures spent, which
model resolved what, and which target tests the failures left failing.

## Output

```
no-harness rows: 18, harness rows: 18

== no-harness (stage 01: one blind call) ==
  verdicts: {'target_still_failing': 12, 'resolved': 4, 'timeout': 2}
  patch applied: 5/18; resolved: 4/18
  by model: haiku 6, sonnet 6, opus 6; resolved by model: opus 3, sonnet 1, haiku 0
  cost: total $5.144, mean $0.2858
  wall-clock: total 1793s, mean 100s
  most-repeated failing target:
    test_decode_correctness::test_kv_cache_logits_match_full_recompute (7)
    test_decode_correctness::test_paged_cache_logits_match_full_recompute (7)
    test_sync_docs::test_angle_brackets_survive_inline_code_verbatim (7)
    test_sync_docs::test_fenced_and_inline_code_are_both_stepped_over (7)

== harness (stage 03: full tool loop) ==
  verdicts: {'resolved': 18}
  patch applied: 0/18 (field absent from the harness log; resolved is the
                  scored outcome)
  resolved: 18/18, by model: haiku 6, sonnet 6, opus 6
  cost: total $9.119, mean $0.5066
  wall-clock: total 1555s, mean 86s
```

## Notes

- 13 of 18 blind calls never resolved; of the 12 target_still_failing, 11
  produced a patch that could not be applied at all (per stage 04's
  taxonomy, which counted them). The dominant no-harness failure is not a
  wrong fix — it is no applicable patch.
- The failures concentrate on four target tests (the decode-correctness
  identity checks and two sync-docs checks), each failing 7 of 18 attempts:
  the blind model cannot reproduce an exact recompute without seeing it.
- Cost per resolution: harness \$0.507/resolved versus blind \$1.286/resolved.
  The loop spends more total (\$9.12 vs \$5.14) and resolves 14 more tasks,
  cheaper per task.
- The tamper guardrail never fired across the 36 real attempts (recorded
  stage 04 finding); this run does not re-count it.
