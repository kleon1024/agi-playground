---
status: verified
level: applied
base: scratch
label: When the traffic is two-sided
verified: 2026-08-07
---

# Switchback: the block unit and the 36-year effect

**Question:** [stage 54's gate](../) flags serial dependence in
time-block experiments. This chapter shows why two-sided settings need
time blocks at all, what block-level analysis costs in detectable effect,
and why the unit is the block, not the request.

**Before this:** [stage 54's gate](../) for the serial-dependence check,
and [ads stage 18 — ad externality](../../../ads/18-ad-externality/) for
the interference mechanism from the supply side.

## Why users cannot be the unit

In a marketplace or ad exchange, randomizing users leaks treatment into
control: a treatment user's purchase consumes shared supply, a changed
ranking moves the equilibrium for everyone, and the two arms no longer
measure the same market. The unit of randomization becomes a time block —
the switchback design. The outcome is a slow-moving market series, and the
run ([record](runs/2026-08-07-switchback.md)) measures what that does to
naive analysis.

## The false positives, executed

Seven days of half-hour blocks, AR(1) market series (phi 0.9), 100
repetitions under the null:

| analysis | false positives | declared alpha |
|---|---:|---:|
| per-minute | 53% | 5% |
| per-block | 3% | 5% |

Per-minute analysis treats 5,040 minutes as independent observations when
the effective unit is 28 blocks: it rejects 53% of null experiments.
Block-level analysis restores near-nominal false-positive control, because
under fair-coin assignment the per-block t-test is close to a
randomization test over the block partition.

## The price, executed

The block unit is coarse. With 28 half-hour blocks, the minimum detectable
effect at 80% power is 0.43 block-SD; a 1% effect needs roughly 36 years
of half-hour blocks. Bojinov, Simchi-Levi and Zhao (2023, Management
Science) formalize the switchback design and its variance inflation;
Uber's engineering practice is the field account of reserving switchback
for marketplace-scale changes. The same run shows the residual risk the
gate flags: with five-minute blocks the block means autocorrelate at a
median lag-1 rho1 of 0.71 — above the gate's 0.2 threshold — and that
autocorrelation is exactly why per-request analysis is catastrophic at any
block length. When block means autocorrelate, the analysis must account
for the serial dependence (time-series-aware standard errors or a model of
the market dynamics), at a further power cost.

## The decision this stage forces

Switchback trades interference for power: it contains the intervention in
time, and the price is an effective sample measured in blocks. The
decision is therefore not "user A/B or switchback" in the abstract — it is
whether the change is large enough and the market interference strong
enough to justify the block unit. Ranking-only tweaks belong in
interleaving ([ads stage 38](../../../ads/38-interleaving-experiments/)),
which compares rankings within the same user session at a fraction of the
traffic; marketplace-wide changes — a fee structure, a matching rule, a
reserve price — belong in switchback, with the timeline priced before the
experiment starts.

## The fix and its trade

The fix is to choose the unit by the interference strength, not by
habit: marketplace-wide changes — a fee structure, a matching rule, a
reserve price — belong in switchback with the timeline priced before the
run, and ranking-only tweaks belong in interleaving, which compares
rankings within the same session at a fraction of the traffic. The
executed run prices the failure: per-minute analysis treats 5,040
minutes as independent when the effective unit is 28 blocks and rejects
53 percent of null experiments, while block-level analysis restores the
declared 5 percent at 3 percent false positives.

The trade is that switchback contains the intervention in time and pays
for it in power: the block unit is coarse, the minimum detectable effect
at 80 percent power is 0.43 block-SD, and a 1 percent effect needs
roughly 36 years of half-hour blocks (Bojinov, Simchi-Levi and Zhao,
Management Science 2023; Uber's engineering practice as the field
account). The block length itself trades autocorrelation against power —
five-minute blocks autocorrelate at rho1 0.71, above the gate's 0.2
threshold — so the decision is made before the experiment starts, when
the interference strength and the effect size are both known.

## Who owns the loop

- **The experimentation-platform team** owns the switchback design, the
  serial-dependence gate, and the block-length choice.
- **The product and marketplace team** declares whether the change is
  marketplace-wide, the call that decides the unit before the run.
- **The analysis team** prices the power timeline before the experiment
  starts, so a small effect never enters a switchback it cannot resolve.

## Evidence boundary

The simulations are synthetic, deterministic, and null (no treatment
effect): they measure the false-positive rate of each analysis and the
power cost of the block unit, not any real marketplace result. Real
switchback design additionally has to handle carryover across blocks
(users persist across the treatment/control boundary — the same problem
as the user-crosses-groups detour, one level up) and the choice of block
length, which trades autocorrelation against power.

## Check your mental model

**1. Per-block analysis restored validity in the run. Why does the gate
still check serial dependence?**

<details>
<summary>Answer</summary>

Because validity under fair-coin assignment is not the same as validity
under every assignment. The simulation's five-minute blocks show block
means autocorrelating at rho1 0.71; if blocks are assigned deterministically
for balance, or the market has longer memory, the block-level standard
error understates the true one. The check exists to force the analysis to
state whether the block series is clean.

</details>

**2. Why is a 1% effect a 36-year experiment under switchback?**

<details>
<summary>Answer</summary>

Because the effective sample is the number of blocks, not the number of
requests: 84 half-hour blocks per arm can resolve only effects around 0.43
block-SD. A 1% lift is far below that, so the timeline to reach 80% power
is measured in decades. This is why the design decision is made before the
experiment: small effects do not belong in switchback.

</details>
