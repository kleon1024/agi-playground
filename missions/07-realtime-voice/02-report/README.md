---
status: verified
level: applied
verified: 2026-07-31
label: Outcome report
---

# Does the serving mechanism built for text transfer to audio, cleanly?

**Before this:** [stage 00](../00-audio-codec/) built a codec that turns a
waveform into a 64-token sequence, and [stage 01](../01-streaming-decode/)
handed that sequence to mission 01's KV-cache decode loop, imported
unmodified, and found it produces identical results to full recompute while
its speed benefit only appears once sequences are long enough to need it.

This stage holds both results against the contract
[`mission.yaml`](../mission.yaml) declared before stage 00 existed. It does
not get to soften the comparison after seeing the numbers.

## The contract, and the answer it produces

`core/report.py` reads stage 00's `codec-seed0.json` and stage 01's
`streaming-seed0.json` directly and checks every acceptance line
mechanically:

```
codec:         MSE 0.0111  vs  silence 0.3251 / mean-signal 0.3001   -> beats both
LM completion: MSE 0.2581  vs  silence 0.3251 / mean-signal 0.3001   -> beats both
oracle (sanity check): MSE 0.0113

quality gap (offline vs streaming): ZERO -- 30/30 clips produced identical
  token sequences (logit-level check, not token-id level)
latency gap: invisible at 48-step native length; a real 6.9x divergence
  (naive) vs 1.3x (cached) at a 500-step stress test

VERDICT: MET
```

`mission.yaml` names five acceptance lines, and the `MET` verdict depends on
all five independently: latency at two scales, the codec and LM beating both
naive baselines, the offline-vs-streaming gap reported explicitly (here, a
true zero -- max logit gap 1.19e-05 across 30 clips), every stage having a
`runs/` entry, and any change to reused serving code being named (none was
needed, itself the finding). Flip any one hypothetically and the verdict
changes -- a codec producing tokens worse than noise would make "the cache
preserves output quality" a vacuous claim regardless of how clean the cache
correctness result was.

<!-- interactive: AcceptanceGatePanel -->

Report-stage code mechanically applying a pre-declared acceptance contract,
refusing to print a verdict when an input is missing, is this repository's
own convention -- the same principle behind pre-registration in empirical
research, standardized through initiatives like the Open Science Framework
(est. 2011) to prevent post-hoc threshold selection.

This is mission 07's first `MET` verdict among the three fully-built
missions this session -- missions 05 (vision) and 06 (game AI) both closed
`NOT MET` on their own honestly-reported results. The difference here is not
luck: the claim mission 07 set out to test (does an *already-proven*
mechanism transfer to a new modality unchanged) is a fundamentally easier bar
to clear than "does training produce a policy that beats a strong baseline"
-- and the report says so plainly rather than treating a `MET` verdict as
evidence this mission was somehow more rigorous than the other two.

## Why the latency finding is reported at two scales, not one

Acceptance requires the offline-vs-streaming gap to be "reported explicitly,
not implied." At this mission's actual 48-token clip length, cached and
naive decode are statistically indistinguishable -- reporting only that
number would understate what the KV cache is actually for. A 500-step
stress test (arbitrary token ids, timing only, the same convention
`engine.py`'s own benchmark uses) shows the real divergence: naive's tail
runs 6.9x slower than its start, cached only 1.3x. Both numbers are real and
both are reported, rather than picking whichever one flatters the mechanism.

## No change to the reused serving code

Acceptance also requires naming any change made to the serving stage's
KV-cache or scheduling code to support audio tokens. None was needed:
`Config`, `Transformer`, `KVCache`, `_forward_with_cache`, and
`build_rope_cache` were imported from `engine.py` and called exactly as
written. This is itself the positive finding mission 07 exists to check for.

## Run it

```bash
cd missions/07-realtime-voice/02-report/core
uv run python report.py
```

`report.py` refuses to print a verdict if either upstream artifact is
missing -- it says `CANNOT DETERMINE` and names exactly which file is
absent, the same discipline this repository's other report stages already
established.

## What this does not establish

No CUDA GPU was available anywhere in this mission's build, so nothing here
is a GPU-lane latency number. Nothing about the paged/continuous-batching
layer specifically, only the single-sequence `KVCache` path. Nothing about
real speech, multi-speaker audio, or sequence lengths beyond the 500-step
synthetic stress test, per `mission.yaml`'s own `does_not_prove`.
