---
status: verified
level: applied
base: scratch
label: When the generator collapses to the train set
verified: 2026-08-08
---

# The generator re-emits the winners, and the cohort has seen them

**Question:** [stage 41's LLM creative generation](../) generates
variants and a scorer picks the delivered winner. This chapter reads
the executed fatigue sweep and asks the failure mode the single scored
batch skips: what happens when the generator keeps re-emitting the top
ads from the historical corpus, so the scorer keeps delivering creative
the cohort has already seen.

**Before this:** [stage 41 — LLM creative generation](../) and its
executed generate-then-select model, plus the
[identical-variants detour](../when-the-generated-creative-is-identical/)
for the collapse at the message level.

## The fatigue sweep, executed

The run ([record](runs/2026-08-08-collapse-fatigue.md)) sweeps the
collapse severity p — the chance each of the 10 generated candidates is
a copy of an existing top ad rather than novel copy — over 4,000
flights of 25 deliveries to one cohort each, with per-ad fatigue (each
re-run of the same ad earns 0.78x the prior CTR):

| collapse p | delivered CTR | re-run share | top-ad lock | decay first-last |
|---|---:|---:|---:|---:|
| 0.0 | 0.0911 | 0.0% | 0.0% | -0.0001 |
| 0.3 | 0.0747 | 33.4% | 33.4% | +0.0221 |
| 0.6 | 0.0515 | 59.8% | 61.1% | +0.0406 |

At collapse 0.6, 59.8 percent of deliveries re-run copy the cohort has
already seen, one corpus ad takes 61.1 percent of the flight, and the
flight's delivered CTR decays 0.0406 from its first block to its last —
the same top creative that converted on first sight earns less every
time it is re-delivered.

## The failure mode, named and audited

**Mode-seeking generation buys fatigue at generation time.** The
generator is trained on the historical corpus, so its preferred mode is
the copy that already worked; when it re-emits that copy, the scorer —
which is also trained on that history — rates it highly and delivers it
again. The scorer is not the villain: in the audit it picks the highest
latent CTR, and the corpus winners genuinely are the strong ads. The
collapse is upstream, in the generator, and the price is paid
downstream, in the cohort: repetition decays response (Keon et al.
2025, "Galton's Law of Mediocrity: Why Large Language Models Regress to
the Mean and Fail at Creativity in Advertising", arXiv:2509.25767,
submitted 2025-09-30 — creative features disappear first under
compression and regeneration "often appeared novel but lacked true
originality").

**The creative wears out before a single new impression is bought.**
Stage 41's economics are that generation is cheap and impressions are
expensive. This audit prices the hidden cost of the cheap step: a
generator that re-runs the corpus spends the expensive impressions on
copy the cohort has already seen, so the pipeline converts a fatigue
problem into a delivery problem. The same fatigue curve exists in
human-produced creative, but LLM generation makes the collapse fast
and silent, because the repeated winner still scores well on the
surface — the sibling failure to the surface-score detour, where the
score rewards the copy's appearance, and here the generator makes the
appearance repeat.

## The fix and its trade

The fix is diversity control at generation plus fatigue awareness at
selection: temperature and repetition penalties push the generator off
its preferred mode, deduplication against the delivered history removes
re-runs before scoring, and the scoring model itself must treat
already-delivered creative as worn (the audit's fatigue factor applied
inside the score, not after delivery). The trade is that both levers
cost coherence and conversion density: pushing temperature up buys
diversity but risks gibberish, and discounting re-runs forces delivery
of copy measurably weaker than the known winner, accepting a lower
expected CTR per impression to keep the cohort responding. The
discipline from stage 16 applies unchanged: the fatigue factor has to
be estimated from delivered impressions, not assumed (Mita et al.
2024, "Striking Gold in Advertising: Standardization and Exploration
of Ad Text Generation", ACL 2024,
aclanthology.org/2024.acl-long.54 — the CAMERA benchmark exists
precisely because ad text lacks a standard feedback loop to score
against).

## Evidence boundary

The executed fatigue sweep over three declared collapse levels
(illustrative, deterministic, fixed seed, assumed fatigue factor)
demonstrates the mechanism; real creative fatigue needs the actual
generator, the real scorer, and measured per-impression CTR over
delivered flights. The Keon et al. and Mita et al. findings are
attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why is the scorer not the cause of the wearout?**

<details>
<summary>Answer</summary>

Because in the audit the scorer picks the highest latent CTR, and the
corpus winners genuinely are the strongest ads. The failure is that the
generator re-emits those winners, so the scorer has nothing novel to
pick — its best choice is the copy the cohort has already seen. The
collapse is upstream in generation; the fatigue is only paid at
delivery.

</details>

**2. Why does generation make this fatigue worse than human creative
rotation?**

<details>
<summary>Answer</summary>

Because the LLM's preferred mode is the corpus — the copy that already
worked — so the generator reproduces the winner by default, at token
cost, at scale. Human teams naturally rotate because the previous
winner is boring to them; the model has no boredom, only mode-seeking.
The audit's top-ad lock shows the result: at collapse 0.6 one ad takes
61.1 percent of the flight's deliveries, so the cohort stops responding
to creative that scored perfectly at generation time.

</details>

## Next

Back to [stage 41](../). The
[surface-score detour](../when-the-score-is-on-surface/) shows the
second failure in the same pipeline: the score that rewards appearance
over measured CTR, which is how a re-run still wins even when the
generator does produce something new.
