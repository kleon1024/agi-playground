# Run — when trust erodes, executed on the opt-out curve

**Date:** 2026-08-07
**Command:** `uv run python core/trust_erodes.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 52's detour: a false explanation is a lie the user can check. This
run reads the opt-out rate as the share of false explanations grows.

## Output

```
trust erodes, read (opt-out rate vs false explanation share):
  false explanations 0%: opt-out rate 1.0%
  false explanations 5%: opt-out rate 1.8%
  false explanations 20%: opt-out rate 5.2%
  false explanations 50%: opt-out rate 13.0%

reading: even a 5% false rate nearly doubles opt-outs;
at 20% a twentieth of users leave. The explanation feature
was meant to build trust, and a wrong one burns it faster
than a missing one - the user can check 'because you
viewed' against their own history, and the check fails.
```

## Notes

- Opt-outs nearly double at a 5% false rate (1.0% to 1.8%) and reach 13.0% at 50%.
- A wrong explanation burns trust faster than a missing one — the user can check the claim against their own history, and the check fails.
