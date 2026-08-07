# Run — epsilon flip rate, does the noise move the budget

**Date:** 2026-08-08
**Command:** `uv run python core/epsilon_flip.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.1s.
**Cost:** \$0 (local lane).

## Purpose

Stage 40's executed draw added noise at epsilon 2.0 and flipped the
display/email order once. This audit asks the industrial question that
single draw skips: how often does that happen? It sweeps epsilon and
measures, over 1,000 fixed-seed draws per level under the stage's own
noise model (uniform noise of range 100 / epsilon on each channel
count), the rate at which the noise flips the display/email pair that
decides the second budget allocation, the rate at which it knocks
search off the top slot, and the rate at which the full order survives.

## Output

```
epsilon flip rate, audited: how often does the noise move budget?
  true counts: search 480, display 310, email 260
  display-email gap: 50
  noise model: stage 40's uniform of range 100/epsilon per count
  1000 fixed-seed draws per epsilon level

epsilon | noise range | display/email flips | top-1 flips | full order kept
   5.00 |      +/-  20.0 |   0.0%        |   0.0%      | 100.0%
   2.00 |      +/-  50.0 |  12.9%        |   0.0%      |  87.1%
   1.00 |      +/- 100.0 |  27.6%        |   0.9%      |  71.5%
   0.50 |      +/- 200.0 |  37.0%        |  16.7%      |  48.0%
   0.25 |      +/- 400.0 |  43.4%        |  31.6%      |  32.4%

reading: the stage's own epsilon 2.0 sits exactly at the
boundary where the close pair can flip. The audit measures
the result: a 12.9% display/email flip rate per report,
so a quarter of 12 weekly reports has a 81% chance of at least one
flipped allocation. At epsilon 5.0 the noise range is smaller
than the 50-count gap and the order never flips. The privacy
dial and the decision-accuracy dial are the same knob: epsilon
must clear the gap that matters (Dwork 2006; differentially
private ad-conversion measurement, PoPETs 2024).
```

## Notes

- 1,000 fixed-seed draws (seed 17) per epsilon level, five levels.
- True counts are the stage's own: search 480, display 310, email 260;
  the display/email gap of 50 is the boundary the audit prices.
- Epsilon 2.0 flips the close pair on 12.9 percent of reports. Over 12
  weekly reports the probability of at least one flipped allocation is
  1 - (1 - 0.129)^12 = 81 percent.
- Epsilon 5.0 keeps the full order on every draw because the noise
  range (+/-20) is smaller than the gap it must protect (50).
- The privacy dial and the decision-accuracy dial are the same knob:
  epsilon must clear the gap that matters.
