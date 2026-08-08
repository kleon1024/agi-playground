# Run: 63 — when the teacher never sees the cut

**Date:** 2026-08-08
**Command:** `uv run python core/cascade_cut.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** about 0.1s.
**Cost:** \$0 (local lane).

## Purpose

Measure what a two-stage cascade re-learns when the teacher — the final
ranker whose score is distilled into the pre-rank — only ever scores the
items that survived the pre-rank's cut. The teacher's score is a saturated
probability (sigmoid of 4 times popularity plus quality, like a pCVR), so
the survivors' labels carry no discrimination and the student is trained
on a truncated, saturated target. Three label regimes run for six
generations each: survivors-only (the failure), full-corpus sample (fix
one: the teacher also scores 400 uniform draws from the rejected corpus),
and stratified sample (fix two: the extra labels are drawn per popularity
group so the tail, which the cut starves hardest, is represented).

## Output

```
== 1. the aggregate, read the way the team can read it ==
catalogue 2,000 items | pre-rank cut 100 | oracle top-50 | teacher score sigmoid(4 x (pop + qual))

student vs teacher correlation on the pairs the teacher scored:
arm                     1       2       3       4       5       6
survivors-only     -0.014  -0.021  -0.021  -0.037   0.001  -0.001
full-corpus sample   0.041   0.037   0.058   0.062   0.070   0.049
stratified sample   0.056   0.060   0.027   0.044   0.037   0.055

== 2. the same students against the full corpus (the read the ==
==    team cannot compute without scoring beyond the cut) ==
arm                     1       2       3       4       5       6
survivors-only      0.715   0.709   0.704   0.697   0.692   0.689
full-corpus sample   0.756   0.756   0.755   0.756   0.756   0.756
stratified sample   0.756   0.756   0.754   0.756   0.756   0.755

== 3. top-K recall at the cut: how much of the oracle's top-50 ==
==    survived this generation's pre-rank ==
arm                     1       2       3       4       5       6
popularity baseline      37      37      37      37      37      37
survivors-only         33      33      33      32      32      32
full-corpus sample      40      40      39      40      39      40
stratified sample      40      40      39      40      39      40

== 4. the final cut, sliced by popularity group ==
arm                  head     mid    tail
survivors-only         93       7       0
full-corpus sample      89      11       0
stratified sample      89      11       0
cut slots from each group; the corpus is 200 head / 800 mid / 1,000 tail

== 5. the funnel closes: oracle top-K items the teacher ever ==
==    scored, cumulative ==
arm                     1       2       3       4       5       6
survivors-only         37      38      38      38      38      38
full-corpus sample      37      42      42      43      43      43
stratified sample      37      42      42      43      43      43

== 6. the verdict ==
the survivors-only cascade starts at 33 of the oracle's top-50
and drifts down to 32, below the 37-of-50 popularity
baseline it was meant to beat. the student's survivor
read is flat near zero (-0.014 -> -0.001)
while its full-corpus read drifts 0.715 -> 0.689,
so the failure trends only in the read the team cannot compute.
scoring beyond the cut recovers the funnel: full-corpus sample
40, stratified sample 40, full-corpus read 0.756.
the teacher ever scored 38 of the oracle's top-50 under
survivors-only labels, 43 with a full-corpus sample, and
43 with a stratified sample. the 12 items it never
scored can never be taught — that blind spot is the funnel this
chapter exists to name.
```

## Notes

- The run is deterministic (seeded stdlib RNG, SEED=93) and the three
  arms share the same generation-0 popularity cut, so the arms are
  comparable: only the teacher-label pool differs. The saturation of the
  teacher score is the compression mechanism — among survivors the labels
  are near one, so the student's fit is driven by survivor feature
  geometry (a noisy popularity proxy) rather than by quality.
- The full-corpus-sample and stratified-sample arms reach the same
  recovery in this read (40 of 50, 43 ever scored); the two differ in
  where the extra teacher budget is spent, not in the recovery ceiling
  here. The stratified repair is the one the literature supports when the
  teacher budget is tight: Kang, Kweon, Lee, Lian, Xie, Yu, "Unbiased
  Knowledge Distillation for Recommendation", WSDM 2023,
  DOI 10.1145/3539597.3570477, shows standard KD propagates and
  intensifies a popularity bias (unpopular-group recall dropping on
  average 22.4% across the KDs they compare, while popular groups rise)
  and proposes partitioning items by popularity and extracting
  within-group ranking knowledge. Verified 2026-08-08.
- Scoring beyond the cut — sampling the teacher over the rejected corpus
  — is the sampling-with-correction direction of Covington, Adams,
  Sargin, "Deep Neural Networks for YouTube Recommendations", RecSys 2016,
  DOI 10.1145/2959100.2959190, applied to distillation labels instead of
  candidate generation. The alternative structural repair, where the
  cheap stage scores the full corpus like the final ranker, is the
  tree-based direction of Zhu et al., "Learning Tree-based Deep Model for
  Recommender Systems", KDD 2018, DOI 10.1145/3219819.3219826. Both
  verified 2026-08-08.
