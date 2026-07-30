---
status: draft
level: foundation
---

# What does a click actually tell you?

**Goal:** turn a logged interaction dataset into a train/test split that does
not lie about how well a model will do, and establish the popularity baseline
every later stage in this mission has to beat.

**Before this:** [why this mission is a funnel](../README.md), for why
recommendation, search, and ads are one decision loop rather than three, and
why that loop is a cascade of progressively more expensive stages over
progressively smaller candidate sets.

**Why this stage decides everything after it.** Every stage downstream of this
one — recall, pre-rank, fine-rank, the value tree — is evaluated against the
split this stage produces. If the split leaks the future into the past, every
later number in this mission is quietly inflated, and no amount of modeling
sophistication downstream can correct for it. This is the one mistake a
from-scratch recommender curriculum has to get right before writing a single
line of ranking code, so it comes first.

## The mistake this stage exists to prevent

Take any interaction log — clicks, ratings, purchases — and split it randomly
into train and test. Train a model on it, and the model will look good: a user
who rated ten action movies highly in March and ten more in April will have
most of those ratings scattered across both splits by chance, and a model that
has memorized March can trivially predict April. That is not personalization.
It is a literal form of cheating — the model has already seen a slice of the
user's future, shuffled a few rows away from the row it is being asked to
predict. A live system never gets to see the future; it ranks items using only
what happened before the moment of the recommendation. A random split is a
mismatch between evaluation and reality that no amount of model quality can
fix, because the mismatch lives in the test, not in the model.

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

## Choose a public dataset, and say why

Two genuinely public options fit this stage, and naming both matters because a
curriculum built around one dataset dies when that dataset does.
[MovieLens](https://grouplens.org/datasets/movielens/) (`ml-latest-small` for a
quick pass, `ml-1m` or `ml-25m` once the pipeline is trusted) ships user, item,
rating, and timestamp in one file — exactly the shape this stage's eligibility
and split logic expects. The
[Amazon Reviews dataset](https://amazon-reviews-2023.github.io/) is the other
standard choice: larger, sparser, with genuinely cold items and a real
popularity long tail, and a useful stress test once MovieLens stops surfacing
new failure modes. This mission builds against MovieLens first, because it is
small enough for later stages — recall in particular — to score every item in
the catalogue exhaustively, which is the property the whole "start mini" plan
depends on.

## Eligibility before quality

`filter_min_interactions` is where this stage's "eligibility, not quality"
rule earns its keep. A user with one rating is not low-quality data — the
rating itself might be perfectly accurate — but there is no way to hold out a
test interaction for that user and still leave a training interaction behind
to learn from. The filter is a fixed point, not one pass: dropping a sparse
item can push a user below threshold, and dropping that user can push another
item below it. `core/interactions.py` loops until nothing changes, capped at a
few passes, because on real logs it converges fast — but only if it actually
loops rather than filtering once and assuming the job is done.

## The split, and the number that makes it undeniable

`time_split` picks one timestamp — wherever the cutoff for the desired test
fraction lands — and assigns every interaction before it to train, every
interaction at or after it to test. No row's user, index, or item identity
matters, only when it happened. `leakage_rate` then answers the leakage
question directly: for every test row, does that same user have a train row
that happened later? For a proper time split the answer is always no, by
construction — every train timestamp sits below the cutoff and every test
timestamp sits at or above it, so a train row can never be later than a test
row for the same user. Run the identical log through `random_split` instead
and that guarantee disappears: a user's ratings scatter across both sides
regardless of order, and a large share of test rows end up with a same-user
train row sitting after them in time. That is not a rounding error or an
artifact of one dataset; it follows directly from the shuffle, and it is the
exact mechanism by which a random split lets a model see its own answer key.

## The floor: popularity

`popularity_ranking` counts train-set item frequency and nothing else — no
user, no query, no signal beyond what already went into the training split.
It is deliberately the crudest possible model, and this mission's
`mission.yaml` names beating it as an acceptance condition, not a footnote: a
system that cannot outperform "show everyone the same popular items" has not
demonstrated personalization, however sophisticated its architecture looks in
isolation. Computing this baseline in the stage that owns the split keeps
every later stage honest against the same train/test boundary, instead of
each stage re-deriving its own.

## Why the log itself is not neutral

Even a leak-free split inherits a subtler problem: every interaction in the
log happened because some earlier system decided to show that item to that
user. A user cannot click something they were never shown, so the log records
the previous ranking policy's decisions as much as it records user
preference. An item that policy buried at position 40 could have been a
user's favorite, and it will never appear as a positive example, because it
was never seen. This is why an offline win on this split — however honestly
measured — cannot be read as "users will actually prefer this," only as "this
ranks the previously-observed interactions better than the baseline does."
The mission's `does_not_prove` section says this plainly, and it starts being
true right here, before a single model exists.

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
instead of Python loops over dataclasses. Run both against the same file and
they agree exactly: same cutoff, same train/test sizes, same leakage count,
same hit rate. That agreement is the point of having two implementations at
all — a production rewrite is worth trusting only once it can be shown to
compute the same thing the readable version does, not merely that it runs
faster. A real pipeline would likely reach for a maintained splitting utility
(`recommenders.datasets.python_splitters`, or `lenskit`'s split module)
instead of the handful of lines this file hand-rolls; reading those lines is
what makes it obvious there is nothing hidden inside that utility beyond this
same cutoff logic.

## Exercises

1. **Quantify the leak on a real dataset.** Download MovieLens
   `ml-latest-small`, run both `time_split` and `random_split` through
   `leakage_rate`, and compare the two leakage counts directly.
2. **Move the cutoff.** Increase `--test-fraction` until the training set
   shrinks enough to visibly hurt the popularity baseline. Find the point
   where the split, not the model, is the bottleneck.
3. **Break the min-interaction filter.** Set `--min-user 1 --min-item 1` and
   inspect what a "test" interaction for a single-interaction user actually
   evaluates — there is no training signal for that user at all.
4. **Read what popularity gets wrong.** List the test interactions the
   popularity ranking misses. Every later stage's job is to recover exactly
   these.

## Next

This split and this popularity baseline are what
[Stage 02 — recall](../02-recall/) is measured against. Stage 01, content
understanding — turning raw item content into embeddings for cold items — is
still planned and will feed recall's two-tower queue once it exists; recall's
from-scratch queues stand in for it for now with synthetic item vectors.
