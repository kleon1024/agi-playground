---
status: verified
level: applied
base: scratch
label: Realtime user state
verified: 2026-08-07
---

# The session is a feature the batch model cannot see

**Question:** stages 43-47 kept the model honest about the world. This
stage asks about the state that changes between requests — what the user
just did — and answers: the session can re-rank the slate before the
batch model would ever be retrained, at the price of computing it per
request.

**Before this:** [stage 08 — serving](../08-serving/) for the two-stage
serving path this state rides on, and [stage 23 — personalized
search](../../search/23-personalized-search/) for per-user state in ranking.

## The batch order versus the session order, executed

The run ([record](runs/2026-08-07-realtime-user-state.md)) ranks six
items for a user who dwelled 40 seconds on an audio item three minutes
ago:

| position | batch (learned ctr) | realtime (session boost) |
|---|---:|---:|
| 1 | P1001 audio 0.032 | P1001 audio 0.041 |
| 2 | P1002 audio 0.030 | P1002 audio 0.039 |
| 3 | P1003 cable 0.028 | P1003 cable 0.028 |
| 4 | P1004 cable 0.025 | P1004 cable 0.025 |
| 5 | P1005 cases 0.020 | P1005 cases 0.020 |
| 6 | P1006 cases 0.018 | P1006 cases 0.018 |

## The mechanism, named

The session pulled audio up and cases down. The batch model would need a
retrain to learn what the session knows from one dwell — the user is
momentarily in an audio mood, and the slate should follow. The trade is
freshness of state against the cost of computing it per request: the
batch path reads learned priors, the realtime path reads live session
signals, and the mix is where the serving decision lives.

## How you find it: the depth-stratified session lift, executed

The boost looks like one number until you split it by session depth.
The run ([record](runs/2026-08-07-realtime-user-state.md)) simulates
400 sessions per depth where the dwelled category matches true interest
with probability q, and the audit
([record](runs/2026-08-07-session-audit.md) —
[`prod/session_audit.py`](prod/session_audit.py)) stratifies the served
CTR the way a serving team reads logged sessions:

| depth | signal q | traffic | batch ctr | realtime ctr | lift | share of lift |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 0% | 0.0090 | 0.0090 | +0.0000 | 0% |
| 1 | 0.50 | 70% | 0.0090 | 0.0156 | +0.0066 | 58% |
| 2 | 0.85 | 20% | 0.0090 | 0.0196 | +0.0106 | 27% |
| 4 | 0.95 | 10% | 0.0090 | 0.0208 | +0.0118 | 15% |

The verdict is SHALLOW SESSION: the single-dwell sessions that own 70%
of traffic earn 56% of the deep-session lift per session. The blended
lift (+0.0079) is what the cost model sees, but the realtime cost is
paid per request for every session, so deep sessions earn the better
ROI — the boost is a function of depth, not a constant. The mechanism
the session-model line of work exploits — session state as a first-class
signal with quality that varies (Hidasi et al., "Session-based
Recommendations with Recurrent Neural Networks", ICLR 2016) — is exactly
what this audit makes operational: stratify the lift before sizing the
spend, and gate the boost on a second signal for depth-1 sessions.

## Who owns the loop

The lift only stays honest if someone owns each side of the trade, and
the handoffs are where the stage's failure modes live:

- **The serving team** owns the request-path feature budget: which
  session signals ride the critical path and the latency each adds (the
  when-realtime-is-too-expensive detour). It owns the cost side of the
  trade.
- **The session-state infrastructure** owns the event stream: freshness,
  ordering, and the feature timestamps the leak detour audits. It owns
  the state side, and its ordering guarantees decide whether the
  features are even usable.
- **The measurement team** owns the stratified lift: the depth split
  that decides whether a signal pays, and the online A/B that confirms
  the offline stratification. It owns the verdict the serving team
  spends against.

When the ownership is implicit, each side optimizes its own number: the
serving team adds features, the infra team stores them without ordering
guarantees, and nobody measures lift per depth — so the request path
fills with signals that do not pay, and the leak goes undetected until
the online A/B fails.

## Why this belongs in the mission

The mission's cascade ends at serving, and serving has a deadline. This
stage is where the pipeline's freshness decisions (43-47) meet the
latency budget (08): realtime state is the freshest feature there is, and
the most expensive to compute. It closes the loop between what the user
does and what the page shows within minutes — the mechanism that makes
the mission's personalization claim true in the moment, not just in the
log.

## Evidence boundary

The executed six-item slate over one declared session (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the session signal's lift against its latency cost per feature, and
decide which signals justify the request-path spend.

## Check your mental model

Answer each before opening it.

**1. Why can the batch model not learn this itself?**

<details>
<summary>Answer</summary>

Because the signal is minutes old: one dwell on an audio item three
minutes ago is below the batch model's retraining horizon and below its
per-user granularity. By the time a retrain could see it, the mood is
gone. The session is a feature whose freshness only the request path can
honor.

</details>

**2. What is the cost of the session order?**

<details>
<summary>Answer</summary>

Computing the state per request: each realtime feature adds latency to
the p95 (the detour measures 38ms to 118ms as the count climbs). The
session boost is only worth it for signals that change fast enough to
justify the critical-path spend — everything else belongs in the batch
path, where it is computed once and reused.

</details>

**3. Why does the traffic-weighted lift sit closer to the depth-1 lift
than the depth-4 lift?**

<details>
<summary>Answer</summary>

Because depth-1 sessions are 70% of traffic, so the blend is dominated
by the weakest per-session signal: +0.0079 sits between the depth-1
lift (+0.0066) and the depth-4 lift (+0.0118). Since the cost is paid
per request for every session, sizing the realtime spend on the blend
hides a nearly 2x ROI difference between the shallow sessions and the
deep ones — which is why the audit stratifies by depth first.

</details>

## Next

The session re-ranks the slate; stage 49 sizes the machine that must
serve it inside the deadline. A detour from here: [realtime is too
expensive once every feature is on the critical path](when-realtime-is-too-expensive/)
— the executed read: p95 climbs 38ms to 118ms as realtime features grow,
and twenty blow through the 100ms deadline.

Another detour: [the session boost decays and the batch order wins
back](when-the-session-state-moves/) — the executed read: two minutes
after the view the boost reorders the slate; by forty minutes the batch
order is back.

A third detour: [the feature window that includes the label window
validates a model that cannot exist](when-the-session-leaks/) — the
executed read: the leaky session feature scores a perfect 300/300 top-1
hit rate offline while the as-of feature the deployed model can
actually use scores 33/300.
