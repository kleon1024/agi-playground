---
status: verified
level: foundation
verified: 2026-07-30
---

# What does a click actually tell you?

**Goal:** turn a logged interaction dataset into a train/test split that does
not lie about how well a model will do, and establish the popularity baseline
every later stage in this mission has to beat.

**Before this:** [why this mission is a funnel](../../README.md), for why
recommendation, search, and ads are one decision loop rather than three, and
why that loop is a cascade of progressively more expensive stages over
progressively smaller candidate sets.

**Why this stage decides everything after it.** Every stage downstream —
recall, pre-rank, fine-rank, the value tree — is evaluated against the split
this stage produces. A split that leaks the future into the past quietly
inflates every later number, and no modeling sophistication downstream
corrects for it. Get this right before writing a single line of ranking
code, so it comes first.

## The mistake this stage exists to prevent

Take any interaction log — clicks, ratings, purchases — and split it randomly
into train and test. Train a model on it, and watch it look good: a user who
rated ten action movies highly in March and ten more in April will have most
of those ratings scattered across both splits by chance, so a model that has
memorized March can trivially predict April. You have not built
personalization. You have let the model cheat — it has already seen a slice
of the user's future, shuffled a few rows away from the row it is being asked
to predict. Remember that a live system never gets to see the future; it
ranks items using only what happened before the moment of the recommendation.
A random split mismatches evaluation against that reality, and no amount of
model quality fixes a mismatch that lives in the test, not in the model.

## What you build

`core/interactions.py` — a from-scratch pipeline in pure Python, no
third-party dependency at all:

| Stage | What it does | Why it exists |
|---|---|---|
| Parse | Read MovieLens-style rows, drop malformed ones | Eligibility comes before any judgment about quality |
| Dedupe | Drop exact (user, item, timestamp) repeats | A retried write is not a second preference signal |
| Min-interaction filter | Iteratively drop users/items below a count threshold | A user or item with one interaction cannot be evaluated at all |
| Time split | One global timestamp cutoff; train before it, test at or after it | The only split that matches how a live system sees data |
| Leakage check | Count test rows whose user has a later train row | Turns "a random split leaks the future" into a number |
| Popularity ranking | Rank items by train-set frequency | The un-personalized floor every later stage must clear |

<!-- interactive: InteractionSplitPipeline -->

## Choose a public dataset, and say why

Two genuinely public options fit here, and naming both matters — a curriculum
built around one dataset dies when that dataset does.
[MovieLens](https://grouplens.org/datasets/movielens/) (`ml-latest-small` for a
quick pass, `ml-1m`/`ml-25m` once trusted) ships user, item, rating, and
timestamp in one file, exactly this stage's expected shape — the dataset and
its collection methodology are documented in Harper & Konstan, *"The
MovieLens Datasets: History and Context"* (ACM TiiS, 2015). The
[Amazon Reviews dataset](https://amazon-reviews-2023.github.io/) is larger,
sparser, with genuinely cold items and a real popularity long tail — a stress
test once MovieLens stops surfacing failure modes. Build against MovieLens
first: it is small enough for recall to score every catalogue item
exhaustively, the property the "start mini" plan depends on.

## Eligibility before quality

`filter_min_interactions` is where this stage's "eligibility, not quality"
rule earns its keep. A user with one rating is not low-quality data — the
rating itself might be perfectly accurate — but there is no way to hold out a
test interaction for that user and still leave a training interaction behind
to learn from. Run the filter and watch it need more than one pass: dropping
a sparse item can push a user below threshold, and dropping that user can
push another item below it. `core/interactions.py` loops until nothing
changes, capped at a few passes — on real logs that converges fast, but only
because it actually loops rather than filtering once and assuming the job is
done.

## The split, and the number that makes it undeniable

Call `time_split`: it picks one timestamp — wherever the cutoff for the
desired test fraction lands — and assigns every interaction before it to
train, at or after it to test, with no row's user, index, or item identity
mattering, only when it happened. Then run `leakage_rate`: for every test
row, does that same user have a train row that happened later? For a proper
time split the answer is always no, by construction — every train timestamp
sits below the cutoff and every test timestamp at or above it. Now run the
identical log through `random_split` instead and watch that guarantee
disappear: ratings scatter across both sides regardless of order, and a
large share of test rows end up with a same-user train row sitting after
them in time — not a rounding error, but the exact mechanism by which a
random split lets a model see its own answer key.

## What the numbers actually look like, on a real dataset

Run this stage against MovieLens `ml-latest-small` (100,836 ratings) and the
abstractions above turn into rows you can point at.
`read_movielens_ratings` parses cleanly — 0 malformed, 0 duplicates — into
rows like `Interaction(user='1', item='1', timestamp=964982703.0,
rating=4.0)`.

`filter_min_interactions` drops 10,562 rows, all for item-sparsity (6,074 of
9,724 movies have under 5 ratings) — and the per-user distribution shows what
the rule alone doesn't: 8 users above MovieLens's own 20-rating guarantee
(user 175 at 24, user 598 at 21, user 578 at 27) fall to 12, 16, and 17 once
their sparse movies are gone. Eligibility moves per item, not just per user.

Interactions per user, after filtering (610 users total):

| bucket | users |
|---|---:|
| 10-19 | 8 |
| 20-49 | 224 |
| 50-99 | 139 |
| 100-199 | 116 |
| 200+ | 123 |

Median 68, min 12, max 2,132.

Now the comparison this chapter argues for, measured instead of asserted.
`time_split` at the default 0.2 test fraction leaks 0 of 1,223 eligible test
rows. `random_split` on the identical interactions leaks 17,885 of 18,055 —
99.1%. One instance: user 75's test row is timestamped 1,158,989,870; that
same user's random-split train set holds a row 369 seconds later. The
popularity floor moves too: hit-rate@20 is 0.0389 under the honest split,
0.0496 under the leaking one — a real number for why comparing scores across
different splits compares different experiments. Full output:
[`runs/2026-07-30-movielens-split.md`](runs/2026-07-30-movielens-split.md).

## The floor: popularity

Call `popularity_ranking` and you get train-set item frequency and nothing
else — no user, no query, no signal beyond what already went into the
training split. That crudeness is deliberate: this mission's `mission.yaml`
names beating this baseline as an acceptance condition, not a footnote, so
keep it in view for every later stage — a system that cannot outperform
"show everyone the same popular items" has not demonstrated personalization,
however sophisticated its architecture looks in isolation. Computing this
baseline once, here, in the stage that owns the split, keeps every later
stage honest against the same train/test boundary, instead of each stage
re-deriving its own.

## Why the log itself is not neutral

Even a leak-free split inherits a subtler problem: every interaction happened
because some earlier system decided to show that item to that user. A user
cannot click something never shown, so the log records the previous ranking
policy's decisions as much as user preference — an item buried at position 40
could have been a favorite, and it never appears as a positive example. An
offline win here, however honestly measured, is not "users will actually
prefer this," only "this ranks the previously-observed interactions better
than the baseline." The mission's `does_not_prove` section says this
plainly, true before a single model exists.

## The fix and its trade

The fix is the time split plus the iterative eligibility filter, and the
recorded run prices both. The time split leaks 0 of 1,223 test rows where a
random split leaks 17,885 of 18,055 (99.1%) — the model never sees the
future, which is the one property a live system is guaranteed to have. The
iterative filter loops until nothing changes, because dropping a sparse item
can push a user below threshold and dropping that user can push another item
below its own; a one-pass filter silently loses users like 175 (24 to 12)
whose own data was fine.

The trade, named: every element of the fix costs volume for honesty. The
filter drops 10,562 rows (6,074 of 9,724 movies have under 5 ratings), and
the time split refuses the extra rows a random split would happily include
as free training data. The popularity floor moves with the boundary too —
hit-rate@20 is 0.0389 under the honest split, 0.0496 under the leaking one —
so the honest number is lower and is the only one every later stage should
be compared against. A team that takes the random split's better-looking
numbers is not saving data; it is comparing the model to a baseline measured
on different rules.

## Who owns the loop

- **The data pipeline team** owns the split contract and the eligibility
  filter: the time cutoff, the min-interaction thresholds, and the loop
  that converges. The leakage count is its regression test.
- **The evaluation team** owns the leakage gate and the popularity floor as
  the acceptance baseline: a model result is only comparable to the floor
  measured on the same split.
- **The model team** inherits the boundary: every downstream model is
  trained and judged inside this stage's split, and a leak that survives
  here inflates every later number regardless of model quality.
- **The logging team** owns what the log records at all — exposure,
  position, and the absence that is a signal (the detour) — because the
  split can only be honest about what the log captured.

## Reproducing

```bash
# offline demo -- no download, no network
python core/interactions.py --synthetic 5000

# against a real file
python core/interactions.py ratings.csv --k 20

# the pandas lane, same contract
pip install pandas
python prod/pandas_pipeline.py ratings.csv --k 20
```

## The production lane, in pandas

`prod/pandas_pipeline.py` does the identical job — parse, dedupe, filter,
split, measure — with `groupby`, boolean masks, and vectorized comparisons
instead of Python loops over dataclasses. Run both against the same file:
they agree exactly, same cutoff, same train/test sizes, same leakage count,
same hit rate. That agreement is the point of having two implementations —
trust a production rewrite once it computes the same thing the readable
version does, not merely because it runs faster. A real pipeline would
likely reach for a maintained splitting utility
(`recommenders.datasets.python_splitters`, or `lenskit`'s split module)
instead of the handful of lines here; reading those lines is what makes it
obvious there is nothing hidden inside that utility beyond this same cutoff
logic.

## Exercises

1. **Quantify the leak on a real dataset.** Run both `time_split` and
   `random_split` through `leakage_rate` on MovieLens `ml-latest-small` and
   compare the two counts directly.
2. **Move the cutoff.** Increase `--test-fraction` until the popularity
   baseline visibly worsens — find the point where the split, not the model,
   is the bottleneck.
3. **Break the min-interaction filter.** Set `--min-user 1 --min-item 1` and
   inspect a "test" interaction for a single-interaction user: no training
   signal exists for that user at all.
4. **Read what popularity gets wrong.** List the test interactions popularity
   misses — every later stage's job is to recover exactly these.

## Next

This split and this popularity baseline are what
[Stage 02 — recall](../02-recall/) is measured against. Stage 01, content
understanding — turning raw item content into embeddings for cold items — is
still planned and will feed recall's two-tower queue once it exists; recall's
from-scratch queues stand in for it for now with synthetic item vectors.

A detour from here: [the 99.1% leak: what the wrong split actually
builds](when-the-split-leaks/) — the recorded split read: the leak is not a
small corruption, it moves the popularity baseline itself (0.0389 vs
0.0496), so scores across splits compare different experiments.

Another detour: [the filter that catches users it did not aim
at](the-eligibility-cascade/) — the recorded cascade read: 8 users fell
below the floor only after their sparse items were removed, which is why
the eligibility filter loops instead of passing once.

A third detour: [the absence is a signal](when-the-absence-is-a-signal/) — the executed log read: a zero click after 1000 exposures is an implicit negative while a zero with zero exposure is silence, so the two zeros must never be merged.
