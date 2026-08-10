# Run — generator collapse to the train set, re-run copy wearout

**Date:** 2026-08-08
**Command:** `uv run python core/collapse_fatigue.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 1.1s.
**Cost:** \$0 (local lane).

## Purpose

Stage 41's generate-then-select pipeline scores generated variants and
delivers the winner. This audit prices the failure the single scored
batch skips: when the generator keeps re-emitting the top ads from the
historical corpus (mode-seeking generation), the scorer keeps picking
those same winners, and the cohort has already seen them — the
delivered creative wears out at generation time, before a single new
impression is bought. It sweeps the collapse severity p (chance each of
the 10 candidates is a copy of an existing top ad rather than novel
copy), runs 4,000 flights of 25 deliveries to one cohort each, and
measures the cohort's mean delivered CTR under per-ad fatigue, the
share of deliveries that re-run copy the cohort has already seen, the
share of the flight taken by the single most-delivered ad, and the
first-block minus last-block CTR.

## Output

```
generator collapse, audited: does re-run copy wear out?
  one flight = 25 deliveries to the same cohort
  per-ad fatigue: each re-run of the same ad earns CTR x 0.78

collapse p | delivered CTR | re-run share | top-ad lock | decay first-last
    0.0 |     0.0911 |        0.0% |        0.0% | -0.0001
    0.3 |     0.0747 |       33.4% |       33.4% | +0.0221
    0.6 |     0.0515 |       59.8% |       61.1% | +0.0406

reading: even with a scorer that picks the highest latent
CTR, mode-seeking generation turns the winner into a re-run:
the cohort has already seen it, so the delivered CTR decays
inside the flight. Diversity controls at generation are not
a style preference — they are what keeps the delivered
creative novel enough to still convert (Keon et al. 2025).
```

## Notes

- 4,000 fixed-seed flights (seed 23) per collapse level; each flight is
  25 deliveries to one cohort. The corpus pool holds three known
  winners with latent CTRs 0.090, 0.084, 0.078.
- At collapse 0.3, 33.4 percent of deliveries re-run copy the cohort
  has already seen and delivered CTR drops from 0.0911 to 0.0747; the
  flight decays 0.0221 from its first block to its last.
- At collapse 0.6 the re-run share reaches 59.8 percent, delivered CTR
  falls to 0.0515, and the flight decays 0.0406; the single top corpus
  ad takes 61.1 percent of the flight's deliveries.
- The scorer is not the villain: it picks the highest latent CTR, and
  the corpus winners genuinely are the strong ads. Mode-seeking
  generation makes the scorer repeat the winner, and repetition is what
  decays the cohort's response — the fatigue is bought at generation
  time (Keon et al. 2025: mode-seeking regeneration fails to recover
  distinctiveness; arXiv:2509.25767).
