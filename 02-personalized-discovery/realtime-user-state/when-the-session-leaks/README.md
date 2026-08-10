---
status: verified
level: applied
base: scratch
label: When the session leaks
verified: 2026-08-07
---

# The feature window that includes the label window validates a model that cannot exist

**Question:** [stage 48's session](../) re-ranks the slate from live
state. This chapter asks what makes a session feature untrustworthy, and
answers: a feature built from the session's own outcome — "clicked this
item later in the session" — scores perfectly offline and does nothing
online, because at serve time the click has not happened yet.

**Before this:** [stage 48 — realtime user state](../) for the session
signals being built, and [stage 44 — the join that looks
ahead](../../44-training-serving-consistency/when-the-join-looks-ahead/)
for the same leak in the label join.

## The leak, executed

The run ([record](runs/2026-08-07-session-leaks-read.md)) scores 300
sessions of ten items with two features: the leaky one (the click
itself) and the as-of one (prior dwells only):

| feature | ndcg@10 | top-1 hits |
|---|---:|---:|
| leaky (clicked in session) | 0.245 | 300/300 |
| as-of (prior dwells) | 0.101 | 33/300 |

## The reading

The leaky feature places the clicked item first in all 300 sessions,
because ranking by "clicked in this session" is ranking by the label.
The eval cannot tell the feature from the outcome, so the model ships
with a perfect top-1 hit rate and produces nothing at serve time, where
the future clicks the feature encodes do not exist. The as-of feature —
events that ended before the target's moment — places the target first
in 33 of 300 sessions: that is the honest number, and it is the one a
deployed model actually earns.

The fix is the time-ordered join, the same discipline stage 44 applied
to labels: every session feature's observation window must end before
the label's window starts. The production tell is the signature of this
class of bug: an offline eval that beats the online A/B by a wide
margin, or a session model that looks excellent in eval and shows no
lift on the request path. When you see that gap, audit the feature
timestamps first — a session feature that knows the future is not
insight, it is the label wearing a costume.

## The fix and its trade

The fix is the time-ordered join, the same discipline stage 44 applies
to labels: every session feature's observation window must end before
the label's window starts, enforced per feature before training. The
executed comparison prices the failure — the leaky feature scores ndcg@10
0.245 with 300/300 top-1 hits, against the honest as-of feature's 0.101
and 33/300, so the leaky model ships excellent and produces nothing at
serve time, where the future clicks it encodes do not exist.

The trade is that the honest feature looks decisively worse offline,
which is exactly why the leak survives review — a team shipping on the
offline number keeps the costume. The repair costs a per-feature
timestamp contract and the discipline to audit before training, and the
production tell is the signature gap: an offline eval that beats the
online A/B by a wide margin, or a session model with no request-path
lift. When that gap appears, the timestamps are the first thing to
audit.

## Who owns the loop

- **The feature-owner team** timestamps each session feature's
  observation window and declares where it ends.
- **The training-platform team** enforces the time-ordered join and
  audits timestamps before every training cut.
- **The measurement team** owns the offline-versus-online gap, the
  signature that tells a leaky feature from a real one.

## Evidence boundary

The executed comparison over 300 declared sessions (illustrative,
deterministic, seeded). It demonstrates the leak and its size; real
systems must audit their own feature timestamps against label timestamps
per feature, because the leak is invisible in the feature's shape — only
the time ordering exposes it.

## Check your mental model

Answer each before opening it.

**1. Why does the leaky feature place the clicked item first in all 300
sessions?**

<details>
<summary>Answer</summary>

Because the feature is the click: "clicked this item in this session" is
constructed from the outcome itself, so ranking by it is ranking by the
label. The model is not predicting the click; it is reading it, and the
eval reports the reading as accuracy.

</details>

**2. How would you spot this leak in a real pipeline?**

<details>
<summary>Answer</summary>

By the signature: an offline eval that beats the online result by a wide
margin, or a model that shows no lift once served. The check is a
time-order audit — whether the feature's observation window ends before
the label's window starts. The leak is invisible in the feature's
distribution; only the timestamps expose it.

</details>

## Next

The session signal is honest; [stage 49 — throughput and
capacity](../../49-throughput-and-capacity/) sizes the machine that must
serve it inside the deadline, where the per-request cost this stage's
audit measured against the lift becomes the capacity number itself.
