# Run — creative selection, executed on the context-ctr model

**Date:** 2026-08-07
**Command:** `uv run python core/creative_choice.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 26 asks which creative an ad shows. This run scores three
creatives per placement context and reads the per-context winner.

## Output

```
creative selection, read:
  video: mobile 0.07 desktop 0.03 -> mobile
  image: mobile 0.04 desktop 0.05 -> desktop
  text: mobile 0.02 desktop 0.02 -> desktop

reading: the video creative wins on mobile, the image on
desktop. Selecting by context instead of a global average lifts
the click rate per placement — the creative is part of the
ad's expected value, which is why it feeds eCPM.
```

## Notes

- The winner is context-dependent: video on mobile, image on desktop.
  A global-average selection would pick video everywhere and leave
  desktop clicks on the table.
- The creative is part of the ad's expected value, which is why it
  feeds eCPM (stage 15) and why stale creative estimates matter.
