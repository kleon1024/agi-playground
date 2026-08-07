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
