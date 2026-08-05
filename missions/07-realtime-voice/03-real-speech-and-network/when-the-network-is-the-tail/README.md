---
status: verified
level: applied
base: scratch
label: When the network is the tail
verified: 2026-08-06
---

# The real network is where the realtime margin goes

**Question:** [stage 03](../) measured a real Tailscale round trip beside
the KV-cache correctness on real speech. A realtime voice contract has two
terms — decode and network — and this chapter reads which one owns the
tail.

**Before this:** [stage 03's real-speech run](../) and the streaming-decode
latency from stage 01.

## The round trip, read

The run ([record](runs/2026-08-06-network-reading.md)) reads the recorded
round-trip JSON:

| | |
|---|---|
| path | Mac -> Tailscale (DERP-relayed) -> remote host |
| pings | 200, 64 bytes each way |
| p50 | 9.66ms |
| p95 | 42.46ms |
| max | 85.25ms |

## Two readings

**The decode side is flat and trustworthy; the network owns the tail.** The
cached path decodes at ~1.5ms/token (stage 01's measured curve), so a
48-token completion is ~72ms of decode with a small, flat network p50
addition (~10ms). But the network's p95 (42.5ms) and max (85.3ms) are
large fractions of the budget — over a DERP-relayed Tailscale path, the
realtime margin is consumed by the network's tail, not by decode. The
realtime contract is a tail contract, and the tail is the network's.

**The correctness check makes the budget question legitimate.** The
KV-cache comparison held on the real-speech vocabulary — max logit gap
~3e-05, 60/60 token sequences matched, the same order as the text
vocabulary — so the decode side is not a correctness risk. The stage can
ask "does the round trip fit the budget" without the cache silently
changing the answer.

## Evidence boundary

One live round-trip measurement (200 pings, DERP-relayed Tailscale); the
decode budget is stage 01's measured curve, cited. It reads the network's
tail against the budget; it does not re-run the round trip and does not
measure a different network path (a direct connection or a different relay
would have different tails).

## Check your mental model

Answer each before opening it.

**1. Why does the realtime budget care about the p95 and max more than the
p50?**

<details>
<summary>Answer</summary>

Because a realtime voice interface is per-call: a single slow round trip is
a broken turn for the user who experiences it, not an average. The p50
(9.7ms) suggests the network is cheap; the p95 (42.5ms) and max (85.3ms)
show the tail where a turn actually stalls. The mission's p50/p95 reporting
rule exists precisely because the tail is what the user meets, and here the
tail is an order of magnitude above the p50.

</details>

**2. The decode is ~72ms for a 48-token completion. Where does the network
fit in a real turn?**

<details>
<summary>Answer</summary>

Per token, the network is cheap — a 9.7ms p50 round trip per 8-token chunk
is small against the chunk's decode. But a turn involves several round
trips, and the network's tail compounds: at p95, each round trip eats 42ms,
and a multi-chunk exchange multiplies it. The decode is flat and bounded;
the network is the variable term, which is why the realtime margin is a
network question after the cache has made decode predictable.

</details>

## Next

Back to [stage 03's real-speech run](../../03-real-speech-and-network/), or
to [stage 04's multi-speaker](../../04-multi-speaker/) where the codec's
health at population scale is the next frontier.
