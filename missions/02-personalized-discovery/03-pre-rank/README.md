---
status: verified
level: applied
label: Pre-rank
verified: 2026-07-30
---

# What can you afford to score, and what must you drop?

**Goal:** cut a candidate set from about a thousand items to about a hundred,
cheaply enough that the expensive fine-ranker in the next stage never has to
touch the rest — and prove that cut is not quietly deciding the outcome on
its own.

Recall handed this stage roughly a thousand candidates it could not afford to
lose. Fine-rank, next, will score perhaps a hundred with a model expensive
enough to earn the name. Between those two numbers sits a stage that has to
be a hundredth the cost of the fine-ranker and still keep the items the
fine-ranker would have chosen — because once an item is cut here, no amount
of fine-ranker quality downstream can bring it back.

**Before this:** [stage 02's five recall queues](../02-recall/) and the
union they hand off — this stage's whole job is to shrink that union without
losing what fine-rank would have picked from it.

## 1. The arithmetic that forces this stage to exist

Try scoring a thousand candidates with fine-rank's model, and you find it is
not merely slower than scoring a hundred — at production latency budgets it
is often not possible at all. Something cheap has to remove most of the
field first, and "cheap" here is not a vague adjective: build a pre-ranker
and it runs at a fraction of fine-rank's per-item cost, using features
already computed (embeddings, simple counts) rather than features that
demand a fresh forward pass through a heavy model. That budget gap is the
entire reason this stage exists as a separate model rather than a cheaper
setting of the fine-ranker.

## 2. What a cheap proxy is allowed to get wrong

Do not ask a pre-ranker to match the fine-ranker's order — ask only that its
cut contains the fine-ranker's eventual top picks. Those are different
requirements, and conflating them is the mistake this lesson exists to
prevent. Let a pre-ranker be noisy everywhere and it can still be fine,
provided the noise does not concentrate on the items that matter. Let it be
**systematically** wrong about a slice of the catalogue, though, and you have
a real problem: systematic error does not average out across a large field
the way random noise does, so a slice that is always underscored never
survives the cut, no matter how good the rest of the ranking looks.

`core/pre_rank.py` makes that distinction concrete with two diagnostics,
computed against `fine_rank_true`, an oracle score the demo's small catalogue
is cheap enough to compute for every item — a luxury a real serving path
does not have, and exactly why it needs a pre-ranker at all.

- **Surface rate** — of the items the oracle actually wants in the true
  top-K, what fraction does the pre-ranker's cut let through? This is the
  number the fine-ranker cannot repair, because it never sees what surface
  rate excludes. `k=10` here on purpose, matching this mission's
  `primary_metric` (nDCG@10, see `mission.yaml`): the diagnostic is measured
  against the thing the mission is ultimately graded on.
- **Rank agreement** — a Spearman correlation between the pre-ranker's order
  and the oracle's, computed only among the items that survived the cut.
  Good agreement with poor surface rate is the dangerous combination: it
  means the pre-ranker orders the field it kept just fine while silently
  discarding a field it never gets credit for having discarded badly.

## 3. A failure mode you cannot see from an aggregate number

`core/pre_rank.py` builds a synthetic catalogue split into `head` items
(established, with logged interaction history) and `long_tail` items (cold,
no interaction history yet). A small share of the long-tail items are
"hidden gems" — genuinely excellent content that has simply never been
shown. The oracle score does not depend on popularity at all, because an
item's fit for a user has nothing to do with how many other people have
already seen it; popularity is generated separately, as a noisy echo of
quality for head items and pure unrelated noise for cold ones, because that
is what popularity actually is in a live system — evidence shaped by
exposure, not a component of relevance.

Two pre-rankers are scored against that oracle. `pre_rank_cheap_proxy`
weighs mostly content similarity, a signal that exists for cold items too,
with a little popularity mixed in. `pre_rank_popularity_only` uses
popularity alone — a common real shortcut, since popularity is already
computed and correlates with quality often enough to look reasonable in
aggregate. Run `pre_rank.py` and compare their **overall** surface rate
against their **long-tail** surface rate specifically. The popularity-only
proxy's long-tail number is not a matter of bad luck on one run: since every
cold item's popularity is uninformative noise by construction, that proxy
cannot distinguish a hidden gem from a mediocre cold item at all, and its
long-tail surface rate will read the same way on every seed. The cheap proxy,
carrying a real content signal, can and sometimes does let a gem through —
imperfectly, but structurally capable of it in a way the popularity-only
proxy is not.

That gap is invisible if you only look at overall rank agreement, which
head items dominate simply by outnumbering long-tail ones. It becomes
visible the moment the metric is sliced by the segment a pre-ranker has no
way to see — which is the entire argument for measuring surface rate by
slice rather than trusting one aggregate correlation.

## What the real run actually shows

Run the default scale (600 items, cut to 60, true top-10) four times, seeds
1/7/42/99:

```
seed  true-top10 long-tail   cheap-proxy long-tail surface   popularity-only long-tail surface
1     9                       0.111                            0.000
7     5                       0.200                            0.000
42    5                       0.200                            0.000
99    7                       0.143                            0.000
```

The popularity-only proxy's long-tail surface rate is **0.000 on every
seed** — exactly the claim above, not a rounded approximation of it: a cold
item's popularity is noise by construction, so it never outranks a head item
on that signal. The cheap proxy's long-tail surface rate is never zero,
because `content_sim` gives it real signal on cold items too.

That gap does not survive every configuration. At the funnel's actual scale
(2000 items, cut to 150, true top-20, seed 42) both proxies hit 0.000 —
the cheap proxy's structural advantage is a capability, not a guarantee at
every cut ratio. Full numbers:
[`runs/2026-07-30-longtail-surface-rate.md`](runs/2026-07-30-longtail-surface-rate.md).

<!-- interactive: PreRankSurfaceRate -->

## Reproducing

```bash
# default: 600-item catalogue, cut to 60, measured against the true top-10
python core/pre_rank.py

# a larger cut, matching the funnel's actual ~1000 -> ~100 ratio more closely
python core/pre_rank.py --catalogue-size 2000 --keep 150 --k 20

# the production lane: a gradient-boosted scorer trained against the same
# oracle, evaluated with the same surface-rate and agreement diagnostics
python prod/lgbm_pre_rank.py
```

## Exercises

1. **Break the cheap proxy on purpose.** Set its popularity weight to 1.0 and
   its content weight to 0 in `pre_rank_cheap_proxy` — it is now
   `pre_rank_popularity_only` in disguise. Confirm its long-tail surface rate
   collapses to match the popularity-only proxy's.
2. **Find where surface rate saturates.** Sweep `--keep` from 20 to 200 at a
   fixed catalogue size and plot surface rate against it. The curve tells you
   how many candidates this pre-ranker actually needs to keep before it stops
   losing true top-K items — a number a real system would tune against
   latency budget, not guess.
3. **Widen the gem share.** Raise `gem_share` in `make_catalogue` and rerun.
   More long-tail items that deserve the top-K make the popularity-only
   proxy's blind spot larger in absolute terms, even though its mechanism —
   zero signal on cold items — has not changed at all.
4. **Compare rank agreement's two failure directions.** Find a parameter
   setting where overall rank agreement is similar between the two proxies
   but their long-tail surface rates diverge sharply. That gap is the exact
   shape of the failure this lesson is about: a healthy-looking average
   hiding a broken slice.

## Next

[Stage 04 — fine-rank](../04-fine-rank/): the model this stage's cut is
protecting. It predicts several objectives at once, which raises a different
problem — whether a shared model trained on all of them helps or hurts each
one individually.
