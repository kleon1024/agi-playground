---
status: verified
level: frontier
verified: 2026-07-29
label: Cheap or expensive
---

# The cheap model resolved everything. Should you use it?

**Question:** you have a resolve rate for three model tiers on the same tasks.
The cheapest one matches the most expensive at a fifth of the price. Is the
routing decision finished?

**The artifact this chapter follows** is two measurements of the same eighteen
attempts:

```text
resolve rate       haiku 6/6    sonnet 6/6    opus 6/6
patch generality   haiku 0/3    sonnet 3/3    opus 3/3
```

By the end you will be able to say what the second row measures, why the
mission's declared primary metric cannot see it, and what it costs to find out.

**Before this:** [stage 02](../02-agent-loop/), which supplies the scorer and
the tasks.

## What the resolve rate says

Two tasks, three tiers, three independent runs each. Every attempt resolved:
target test green, nothing that passed before failing after, no patch touching
a test file.

| Model | Resolve | \$/resolved | Median wall-clock |
|---|---|---|---|
| haiku | 6/6 | **\$0.1604** | 64 s / 120 s |
| sonnet | 6/6 | \$0.5369 | 41 s / 98 s |
| opus | 6/6 | \$0.8226 | 75 s / 85 s |

Read on its own, this settles the mission's decision: route everything to the
cheapest tier and spend a fifth as much. It also makes the more expensive tiers
look actively wasteful, since haiku is only slower, never worse.

Note in passing that cost and latency do not move together — haiku is the
cheapest and, on the harder task, the slowest, because it takes more turns to
get there. A cost-optimal policy and a latency-optimal policy are not the same
policy.

## What the diffs say

All eighteen attempts were kept as patches, and the nine for the harder task
fall into three strategies, split cleanly by tier.

**Opus** imported `torch.nn.attention.bias.causal_lower_right` — the same
construct as the original fix. **Sonnet** wrote its own equivalent boolean
mask. **Haiku** switched masking off during decode:

```python
is_causal = (start_pos == 0)
out = F.scaled_dot_product_attention(q, k_full, v_full, is_causal=is_causal)
```

That is correct when the query is a single token. Every cached key is then in
the past by construction, so there is nothing left to mask and the flag is
redundant. It stops being correct the moment a multi-token query meets a
non-empty cache, because nothing then prevents a query from attending to a key
later in its own block — the one thing a causal mask exists to prevent.

The target test runs a prefill and then single-token decode steps. **It never
produces that shape.**

## Measuring the gap the test leaves

[`core/probe_generality.py`](core/probe_generality.py) sends a 4-token query
against a cache holding 6 and compares against a full recompute, at the same
2e-5 tolerance the target test uses. It checks the single-token shape too, so a
failure cannot be confused with a patch that is simply broken.

| Patch | Single-token decode | 4-token query on a live cache |
|---|---|---|
| the original fix (control) | 5.960e-08 ok | 5.960e-08 ok |
| haiku, all three runs | 5.960e-08 ok | **1.2e-03, 4.2e-02, 1.2e-03 wrong** |
| sonnet, all three runs | 5.960e-08 ok | 5.960e-08 ok |
| opus, all three runs | 5.960e-08 ok | 5.960e-08 ok |

Haiku 0/3, sonnet 3/3, opus 3/3 — against a resolve rate that reads 18/18.

## Why this was predictable

It is the original bug displaced by one shape.

`is_causal=True` built the mask top-left, which is right when query and key
lengths match — prefill — and wrong when they do not — decode. The test was
written from that failure. Haiku's patch is right for decode and wrong for a
multi-token query, which is the neighbouring case the test does not reach.

A test written from one observed failure teaches a fix to cover that failure.
Nothing in an agent loop asks for more, because nothing in the loop can see
past the scoreboard it is optimising. The stronger tiers did not pass a check
the weaker one failed; they generalised without being asked to, and the harness
had no way to notice either way.

Worked in shapes, and verified directly against PyTorch's actual behavior
(not re-derived abstractly): haiku's decode branch uses `is_causal=False`
once `start_pos != 0` -- during decode, nothing is masked at all. At
single-token decode (a 6-token cache, 1 new token, mask shape 1x7), that
matches the correct bottom-right-causal mask exactly -- every cached key
legitimately precedes the one new token, so leaving everything open produces
the same result as masking correctly, 0 mismatches. At the probe's actual
4-token query (mask shape 4x10), it does not: the correct mask still blocks
each new-block query from seeing *later* new-block positions (row 0 may not
see new-block columns 1-3, row 1 may not see columns 2-3, and so on), but
`is_causal=False` leaves all of them open regardless. Row 0 has 3 wrongly-open
cells, row 1 has 2, row 2 has 1, row 3 (the last position, which legitimately
can see everything) has 0 -- 6 wrongly-open cells total, and this is the
direct cause of haiku's 1.2e-3/4.2e-2/1.2e-3 measured errors: a query
attending to a key that is, from its own position, still in the future.

<!-- interactive: DecodeMaskShape -->

The top-left-vs-bottom-right causal-mask convention split is a real, dated
API distinction: PyTorch added `torch.nn.attention.bias.causal_lower_right`
in the 2.5 release cycle (2024) to give decode-time attention (query shorter
than key) a correct default, after FlashAttention-style fused kernels (Dao et
al., 2022) made bottom-right alignment standard for cached decode.

## What this costs the maintainer

The decision the mission set out to make now has two answers.

By resolve rate: always route to the cheapest tier, five times cheaper, no
measured loss.

By patch generality: the cheapest tier produced three latent defects that a
maintainer reading a green test run would merge.

Neither answer is wrong. They measure different things, and the mission
declared the first one as primary before seeing either — which is the point of
declaring it in advance, and also the reason the declaration is not the last
word. A primary metric bounds what you may claim; it does not bound what you
are allowed to look at.

## What this does not prove

**Haiku's patch is not wrong for this repository today.** `generate` only ever
issues a prefill followed by single tokens, so every existing call site sits
inside the range where the patch holds. It breaks when someone adds chunked
prefill, speculative decoding, or prefix-cache reuse. Latent, not live.

**The probe was written after reading the diffs.** That is the right order for
finding a failure mode and the wrong one for estimating how often it occurs.
Nothing here supports a rate.

**Two tasks, one bug class, one probe.** `haiku`, `sonnet`, and `opus` are
aliases the CLI resolved on 2026-07-29, not pinned weights. Dollar figures are
list-price equivalents reported by the CLI on a subscription; the ratios
between tiers are the durable part. Full boundary in
[`runs/`](runs/2026-07-29-model-tier.md).

**Nothing about the harness.** These ran through Claude Code's own loop, not
the from-scratch harness in [stage 02](../02-agent-loop/). Whether a loop beats
a single blind call is still unmeasured — that is stage 01.

## Check your mental model

1. The resolve rate is 18/18 and the patch generality is 6/9. What is the
   difference between the two measurements measuring?

<details>
<summary>Answer</summary>

The resolve rate asks whether the target test goes from red to green, using
exactly the input shape the test exercises: single-token decode. The patch
generality asks whether the fix holds on a shape the test never checks —
`probe_generality.py`'s 4-token query against a live cache. Both are real
measurements; they are just measuring different questions, and a scorer that
only runs the target test cannot see the second one at all. That is why
haiku can score 6/6 on resolve rate and 0/3 on generality without either
number being wrong.

</details>

2. Why can a test written from one failure not distinguish a narrow fix from a
   general one?

<details>
<summary>Answer</summary>

Because the test was written by observing a specific failure — prefill
versus decode shape mismatch — and it only encodes enough input to reproduce
that one shape. A fix that happens to be correct exactly on that shape and
wrong everywhere else passes the same test as a fix that is correct
everywhere. Haiku's `is_causal=False` branch is the proof: it matches the
single-token decode case the test runs (nothing to mask, so leaving
everything open is harmless) and silently fails the 4-token case the test
never runs. The test can only tell you the bug you already knew about is
fixed, not whether the neighbouring case is.

</details>

3. Haiku's patch is wrong for a shape no current call site produces. What makes
   that worth reporting, and what makes it wrong to call it a live bug?

<details>
<summary>Answer</summary>

It's worth reporting because it's a latent defect: `generate` only issues a
prefill followed by single tokens today, but the moment someone adds chunked
prefill, speculative decoding, or prefix-cache reuse, the exact 4-token-query
shape the probe already measured as wrong (1.2e-3/4.2e-2/1.2e-3 error) starts
occurring for real. It's wrong to call it live because nothing in this
repository's current call sites actually produces that shape yet — the "What
this does not prove" section states this directly: latent, not live. The
distinction matters because reporting it as an active bug would overstate
what was actually observed; reporting nothing would hide a defect a future
change could trip over.

</details>

4. Cost and latency ranked the three tiers differently. Which policy does the
   mission's stakeholder actually need, and why is that not settled here?

<details>
<summary>Answer</summary>

The table shows haiku cheapest but slowest on the harder task (120s median),
sonnet fastest (98s) despite costing 3.3x more, and opus in between on both —
so "cheapest" and "fastest" name two different policies, not one. Which the
stakeholder needs depends on whether the routing decision is optimizing
dollar spend or wall-clock latency, and this chapter does not settle that
because `mission.yaml`'s declared primary metric is resolve rate, not either
of these — the cost/latency tradeoff is a real finding surfaced here, not the
thing the mission was built to decide between.

</details>

**Next:** stage 01 strips the loop to a single blind model call, which is the
control that says whether tools and test feedback are worth their complexity.
Stage 04 catalogues failures by category — and this chapter has just supplied
the first category that the scorer cannot detect on its own.

A detour from here: [when every tier resolves everything, which tier
won?](the-tier-that-won/) — the recorded 18/18 laid out as economics: haiku
at 10.6% of total cost, working harder (more tokens, more turns) to get
there.
