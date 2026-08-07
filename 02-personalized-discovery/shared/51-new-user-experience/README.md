---
status: verified
level: applied
base: scratch
label: New-user experience
verified: 2026-08-07
---

# The first page is decided before personalization can see the user

**Question:** stages 02-08 personalized from interaction logs. This stage
asks what to serve before the logs exist, and answers: a recommender
needs interactions to personalize, and a new user has none — the first
page is served by a default, and onboarding priors can shorten the runway
only if they are right.

**Before this:** [stage 02 — recall](../02-recall/) for the cold items,
and [stage 33 — multimodal recall](../../recommendation/33-multimodal-recall/) for the
content-side cold start this user-side problem mirrors.

## The runway, executed

The run ([record](runs/2026-08-07-new-user-experience.md)) measures
NDCG@10 against the user's true taste as interactions accumulate:

| policy | ndcg@10 |
|---|---:|
| popularity only | 0.122 |
| personalized after 1 interaction | 0.429 |
| personalized after 5 interactions | 0.694 |
| personalized after 20 interactions | 0.878 |

## The mechanism, named

At zero interactions personalization has no signal, so popularity is the
serving policy and the first page is a default decision. The trail
improves NDCG from 0.122 to 0.878 over twenty interactions — a short
runway, but one that must be bridged. Onboarding priors are the lever
that moves the first page before the trail exists: they inject a guess
about taste, and the detours show both what a right guess buys (0.878)
and what a wrong one costs (0.000).

## How you find it: the onboarding-path cohort, executed

The first-page number looks healthy until you split it by how new users
arrived. The run ([record](runs/2026-08-07-new-user-experience.md))
emits per-path first-page rows, and the audit
([record](runs/2026-08-07-cold-start-audit.md) —
[`prod/cold_start_audit.py`](prod/cold_start_audit.py)) compares each
path against the popularity default and the no-ask baseline, the way a
growth team reads acquisition funnels:

| path | traffic | first-page ndcg | vs 0.122 | retention | vs no-ask |
|---|---:|---:|---:|---:|---:|
| popularity | 60% | 0.122 | +0.000 | 0.24 | +0.04 |
| right prior | 20% | 0.878 | +0.756 | 0.55 | +0.35 |
| wrong prior | 10% | 0.000 | −0.122 | 0.18 | −0.02 |
| no-ask | 10% | 0.050 | −0.072 | 0.20 | +0.00 |
| aggregate | 100% | 0.254 | +0.132 | 0.29 | +0.09 |

The verdict is NEW-USER GAP: the wrong-prior path serves 0.000
first-page relevance — below the 0.122 popularity default — and earns
0.18 retention, below the 0.20 no-ask baseline. A confident wrong prior
is worse than asking nothing. The aggregate (0.254) hides it because
60% of new users arrive via popularity, which scores exactly at the
baseline; stratify by onboarding path before declaring the first-page
policy healthy, and route a failing path back to the default while its
prior is re-measured. The cold-start literature names this the
prior-quality problem: a wrong system-side assumption about the user
can sink relevance below the no-signal default (Abdullah et al.,
"Eliciting Auxiliary Information for Cold Start User Recommendation: A
Survey", Applied Sciences 2021).

## Who owns the loop

The first page only improves if someone owns each side of the runway,
and the handoffs are where the stage's failure modes live:

- **The growth or acquisition team** owns the onboarding paths and the
  traffic split between them: which questions are asked, which defaults
  are served, and the share of new users each path receives. It owns
  the traffic side of the cohort audit.
- **The cold-start ranking team** owns the priors and the exploration
  budget: the prior's accuracy, the strength of its boost, and whether
  exploration repays itself on the measured runway. It owns the
  relevance side of the first page.
- **The measurement team** owns first-page NDCG and D7 retention per
  path: the stratification that exposes a path performing worse than
  doing nothing, and the routing decision that pulls a failing path
  back to the default. It owns the verdict the growth team routes on.

When the ownership is implicit, each side optimizes its own number: the
growth team drives signup volume, the ranking team tunes the prior in
the aggregate, and nobody measures first-page relevance per path — so
the wrong-prior path grows its traffic share while its retention
number drops, and the platform blames the wrong stage.

## Why this belongs in the mission

The mission promises "users found things faster". A new user is where
that promise is most fragile: the cascade's personalization machinery
needs data this user has not produced yet. The first page is the moment
the mission is judged by a user who has given nothing, so the cold-start
policy is not an edge case — it is the acquisition funnel's ranking
decision, and the lever that decides whether the mission's personalization
ever gets a second visit to learn from.

## Evidence boundary

The executed NDCG progression over declared interactions (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the actual runway length per surface, the retention cost of a wrong first
page, and the onboarding prior's accuracy before trusting it.

## Check your mental model

Answer each before opening it.

**1. Why does popularity score 0.122 instead of 0?**

<details>
<summary>Answer</summary>

Because popularity is not random — popular items match the average user
some of the time. For a new user, it is the best available estimate of
taste, which is why it is the serving default. The number matters as the
baseline: every personalization policy is compared against it, and a
system that cannot beat 0.122 on the first page has not earned the
right to personalize at all.

</details>

**2. What is the runway, exactly?**

<details>
<summary>Answer</summary>

The number of interactions a user must produce before personalization
outperforms popularity. Here it is about 20 interactions to reach 0.878;
the runway is the gap the first-page policy must bridge. Shortening it —
with priors, exploration, or shared user segments — is the entire
cold-start design problem, and each lever has its own failure mode, which
the detours measure.

</details>

**3. Why does the aggregate 0.254 hide the failing path?**

<details>
<summary>Answer</summary>

Because the aggregate weights each path by its traffic share, and 60% of
new users arrive via popularity, which scores exactly at the 0.122
baseline. The wrong-prior path — the only one that loses relevance and
retention — carries just 10% of traffic, so its 0.000 first-page NDCG
moves the blend by only −0.012. A path that underperforms doing nothing
is invisible in the blend until you stratify by onboarding path, which
is why the audit compares each path against the no-ask baseline rather
than the aggregate.

</details>

## Next

The runway is bridged by priors or exploration; stage 52 asks what the
user must be able to verify about the resulting page. A detour from here:
[a confident prior reads as a misread](when-personalization-scares/) — the
executed read: a strong onboarding prior pushes the chosen category from
a fifth to two-fifths of the first page.

Another detour: [the onboarding prior is a bet on an answer the user may
not mean](when-the-user-is-new/) — the executed read: the right prior
lifts the first page from 0.122 to 0.878, the wrong one collapses it to
0.000.

A third detour: [exploration is a price paid during the
runway](when-the-bandit-explores/) — the executed read: greedy from a
popularity-initialized estimate pays nothing (0.817 runway average), a
fixed 10% exploration budget costs 0.022, and 30% costs 0.090, so on a
short horizon the prior moves the first page more than the exploration
budget does.
