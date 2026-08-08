---
status: verified
level: applied
base: scratch
label: When the logits match
verified: 2026-08-06
---

# The zero gap is checked at logit level, not token level

**Question:** [stage 01's streaming decode](../) claims cached decode
equals full recompute. This chapter reads the recorded correctness check
and asks why the comparison is made at logits.

**Before this:** [stage 01's streaming decode](../) and its recorded JSON.

## The check, read

The run ([record](runs/2026-08-06-logit-read.md)) reads the recorded
numbers:

| metric | value |
|---|---|
| clips with identical tokens | 30/30 |
| max logit gap | 1.19e-05 |
| mean logit gap | 5.27e-06 |

## Two readings

**Identical tokens could hide a confidence shift, so the check is at
logits.** Two decodes could emit the same token ids with different
probabilities — token equality alone would call that "identical." The
max logit gap (1.19e-05) is machine-epsilon-scale noise, which is the
only reading that makes "identical" a precise claim rather than a
coincidence.

**The zero quality gap is what makes the latency win a pure win.** If the
cache produced different output, the speedup would be a different model,
not an optimization. The logit-level zero is the precondition that lets
stage 02's latency numbers be read as a pure win — and it is why the
report states the gap explicitly rather than assuming it.

## The fix and its trade

The fix is checking identity at logit level, not token level: two decodes
can emit the same token ids with different probabilities, so token equality
alone would call a confidence shift "identical" — the max logit gap
(1.19e-05, mean 5.27e-06) at machine-epsilon scale is the only reading that
makes "identical" a precise claim. The trade is that the check is stronger
than a token-id comparison and therefore the load-bearing one: a real
divergence would first show up here, before any token id flipped, and a
nonzero gap would mean the cache changes the model — the speedup would be a
different model, not an optimization, and stage 02's verdict would not be
clean.

## Who owns this loop

- **The eval owner** owns the logit-level protocol and the repo's own
  tolerance (`TOL=2e-5`); the comparison follows the same methodology the
  text test uses, never a weaker ad-hoc check.
- **The serving owner** owns the cache's behavior-preservation contract:
  the zero gap is a property of the implementation, verified, not assumed.
- **The report owner** owns the load-bearing line: the logit-level zero is
  what lets stage 02's latency numbers be read as a pure win, and it is
  stated explicitly in the verdict rather than implied.

## Evidence boundary

The recorded streaming JSON (30 clips, one seed, logit-level comparison,
the repo's own tolerance). It reads that artifact; it does not re-run the
decode.

## Check your mental model

Answer each before opening it.

**1. Why is token-level equality not enough?**

<details>
<summary>Answer</summary>

Because the cache is supposed to preserve the model's behavior exactly.
Two decodes that emit the same tokens but with different probabilities
are not equivalent — the confidence could shift even if the argmax does
not. The logit-level comparison catches that shift; a max gap of 1e-5 is
the evidence that nothing moved beyond floating-point noise.

</details>

**2. What would a nonzero logit gap mean for the verdict?**

<details>
<summary>Answer</summary>

It would mean the cache changes the model, and the speedup would not be a
pure win — faster at a cost in behavior. The recorded gap (1e-5) is what
keeps the verdict clean; any real divergence would first show up here,
before token ids diverged, which is why the check is the load-bearing
one in stage 02's five lines.

</details>

## Next

Back to [stage 01](../), or to
[the KV cache on audio tokens: same answer, flat latency](../when-the-cache-pays/)
which reads the same run's latency side.
