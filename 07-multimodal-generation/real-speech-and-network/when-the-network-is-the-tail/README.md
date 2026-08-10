---
status: verified
level: applied
base: scratch
label: When the network is the tail
verified: 2026-08-06
---

# The realtime margin is the network's tail

**Question:** [stage 03's real speech and network](../) moved the mission
from synthetic tones to real speech over a real network. This chapter
reads the recorded ping timing and asks where the realtime budget goes.

**Before this:** [stage 03's real speech and network](../) and its recorded
ping run.

## The round trip, read

The run ([record](runs/2026-08-06-network-tail-read.md)) reads the
recorded distribution:

| metric | value |
|---|---:|
| p50 | 9.7 ms |
| p95 | 42.5 ms |
| max | 85.3 ms |
| p95/p50 | 4.4x |

200 pings, 64 bytes each way.

## Two readings

**A 48-token completion decodes in ~72ms on this lane; the network is the
variable part.** The codec and LM are millisecond-scale and mostly flat;
the network round-trip spans 6-85ms. The p50 (9.7ms) is a small addition
to the decode, but the p95 (42.5ms) and max (85.3ms) are a significant
fraction of any realtime budget. The tail is where the realtime contract
lives — and the p95/p50 ratio of 4.4x is the variance a budget must
absorb.

**The network, not the codec, decides whether realtime is met.** Stage 02's
MET was about the serving mechanism on synthetic tones; stage 03 adds the
real-world constraint the mechanism sits under. The recorded distribution
is the evidence that the bottleneck moved: local decode is tight, the
network is not, and any end-to-end latency claim has to be made against
the tail, not the mean.

## The fix and its trade

The fix is reporting the latency distribution, not the mean: a realtime
service fails on the slow requests, so the budget is set by the tail — the
recorded 200-ping round trip (p50 9.7ms, p95 42.5ms, max 85.3ms, a 4.4x
p95/p50 ratio) is what a 48-token completion's ~72ms decode budget must
absorb. The trade is that the number is path- and day-specific: one host,
one session, one DERP-relayed Tailscale path, so it does not generalize to
arbitrary internet paths — and the fix's value is redirecting the
optimization: since the network variance dominates the end-to-end tail,
another microsecond of decode buys little, and the lever is
network-side (closer deployment, fewer hops, or a budget that tolerates
the p95).

## Who owns this loop

- **The network owner** owns the ping protocol and its scoping: 200 round
  trips, 64 bytes each way, one path, reported as this link's numbers on
  this day.
- **The serving owner** owns the decode budget the network sits under; the
  split is what keeps local latency and network latency as two honestly
  distinguished numbers.
- **The mission owner** owns the realtime contract: the p95/max, not the
  mean, is the acceptance-relevant tail, and stage 03 exists because a
  mechanism-only MET says nothing about the real constraint it runs under.

## Evidence boundary

The recorded ping run (200 pings, one host, 64 bytes each way, one
session). It reads that artifact; it does not re-ping and the numbers
characterize this network path on this day.

## Check your mental model

Answer each before opening it.

**1. Why does the p95 matter more than the mean here?**

<details>
<summary>Answer</summary>

Because a realtime service fails on the slow requests, not the typical
one. The mean round trip (15.1ms) looks fine beside the decode; the p95
(42.5ms) and max (85.3ms) are where requests actually break a latency
budget. A budget set from the mean would miss the 5% of requests that
take 4.4x the median — the tail is the contract.

</details>

**2. What does the decode-vs-network split imply for an optimization?**

<details>
<summary>Answer</summary>

That optimizing the codec further buys little, because the network
variance dominates the end-to-end tail. The lever is network-side —
closer deployment, fewer hops, or a budget that tolerates the p95 — not
another microsecond of decode. The recorded split is what redirects the
optimization from the serving mechanism to the path it runs over.

</details>

## Next

Back to [stage 03](../), or to
[the real network is where the realtime margin goes]()
which reads the same run's end-to-end story.
