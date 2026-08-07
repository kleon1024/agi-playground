---
status: verified
level: applied
base: scratch
label: Interleaving experiments
verified: 2026-08-07
---

# The blended list can hand the win to whichever team got the better positions

**Question:** every measurement stage so far compared groups of users.
This stage asks how to compare two rankings with a fraction of the
traffic and answers: interleaving — both users see one blended list,
and clicks credit the team that proposed each clicked result. The
audit then asks the industrial question the mechanism skips: the teams
are equal, so why does one team walk away with the win?

**Before this:** [stage 24 — search measurement](../../search/24-search-measurement/)
for the offline-versus-online gap, and [stage 30 —
ads measurement](../30-ads-measurement/) for the control-group
discipline interleaving replaces with a within-user comparison.

## The credit, executed

The run ([record](runs/2026-08-07-interleaving-experiments.md))
interleaves two teams' rankings:

| team | proposed list |
|---|---|
| a | d1, d2, d3 |
| b | d4, d2, d5 |
| interleaved | d1, d4, d2, d3, d5 |
| clicks | d4, d2 |
| credit | team a 1, team b 2 |

## The mechanism, named

Both teams propose a ranking; the system blends them into one list and
shows every user the same interleaved list. Each click credits the team
that proposed the clicked result — d4 credits b, d2 credits a, so b
wins on its exclusive proposal. Because both ranking variants appear
inside the same user session, the comparison cancels user-level noise,
which is why interleaving needs far fewer users than a between-user
A/B.

## The failure mode, named and audited

**The blend, not the ranking, decides who gets the win.** The audit
([record](runs/2026-08-08-interleave-position.md)) simulates 10,000
sessions over the stage's own position click model — slots 1 through 6
click with probabilities 0.30, 0.20, 0.14, 0.10, 0.07, 0.05 — with
equal teams and disjoint proposals, so every credited difference comes
from the blend:

| blend policy | credited share, team A | credited share, team B | verdict |
|---|---:|---:|---|
| naive (team A starts every session) | 59.2% | 40.8% | the blend hands A the win |
| balanced (random start per session) | 49.7% | 50.3% | equal teams, equal credit |

The naive list gives team A positions 1, 3, 5, whose click mass sums to
0.51, and team B positions 2, 4, 6 (0.35) — so A is credited with 59.2
percent of clicked sessions despite proposing nothing better. Users
click whatever sits near the top independent of quality (Joachims et
al., 2005, SIGIR), and a blend that hands one team the better slots
credits clicks that team did not earn. The fix is the random start, and
the [blend-bias detour](when-the-blend-biases-the-credit/) measures the
trade instead of asserting it: across 2,000 experiments the naive mean
is 59.3 percent against 50.0 percent for the balanced policy, at
200,000 sessions the naive interval is +/-0.23 percent around 59.3
percent — 78 standard errors from the true 50/50 — and the random start
costs exactly 3.6 percent more sessions for the same interval width.
Interleaving's sensitivity advantage is why the design is worth this
care: interleaving is the most sensitive of the compared metrics in
Radlinski & Craswell (2010, SIGIR), roughly one to two orders of
magnitude more sensitive than a between-user A/B on the same traffic
(Schuth, Hofmann & Radlinski, 2015, SIGIR), and production teams lean
on it for exactly that reason — Airbnb ships search-ranking changes off
interleaving plus counterfactual evaluation (Zhang et al., 2025,
arXiv:2508.00751), and the Spotify confidence glossary states directly
that interleaving is "dramatically more sensitive than traditional A/B
testing for ranking problems."

## Who owns the loop

Interleaving only produces an honest answer if someone owns each side
of the within-user comparison, and each owner is tied to one failure
mode above:

- **The ranking team** owns the blend: which interleaving method, which
  teams are compared, and how the lists are merged into one session.
  It owns the blend-bias failure — the audit measured a fixed 9.2-point
  credit swing that more traffic never shrinks, and the fix (random
  start) costs 3.6 percent more sessions for the same interval width.
- **The experimentation and measurement team** owns the credit model:
  the tie rule for shared documents, the pooled statistical test over
  credits, and the pre-registered start randomization. It owns the
  tie-ambiguity failure — a click on a document both teams proposed
  credits both unless a rule decides it (Radlinski, Kurup & Joachims,
  2008, CIKM; Chapelle et al., 2012, TOIS).
- **The traffic owner** owns the budget the design consumes. It owns
  the tiny-traffic failure — the between-user A/B that needs 10,000
  users where interleaving needs 400, and the B2B (business-to-business)
  risk of shipping a ranking change unmeasured because the A/B never
  reaches significance.

When the ownership is implicit, the ranking team ships the naive blend,
the measurement team reads the 59.2 percent as a ranking win, and the
traffic owner pays for an experiment whose answer is a property of the
blend — the audit's 59.2/40.8 split is that experiment: equal teams,
one winner, and the winner is the position assignment.

## Why this belongs in the mission

The mission's funnel changes ranking constantly, and the old comparison
costs traffic the product cannot spare. Interleaving is how ranking
teams ship changes with limited traffic — the tiny-traffic detour shows
an A/B needs 10,000 users where interleaving needs 400. The frontier
claim is that measurement can be faster without being weaker, and the
audit adds the industrial detail that claim skips: a faster experiment
is only worth its answer, and the answer is decided by the blend, the
tie rule, and the start randomization — three decisions the ranking
team, the measurement team, and the traffic owner each own.

## Evidence boundary

The executed interleave over two hand-built rankings with declared
clicks (illustrative, deterministic, assumed click sequence). It
demonstrates the mechanism; real interleaving needs the blending
algorithm, the tie rule, and a statistical test over the credits, which
the detours quantify. The audit's simulations (fixed seed, declared
position click probabilities) are illustrative and deterministic; the
Airbnb, Spotify, and Radlinski & Craswell sensitivity claims are
attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why does interleaving need far fewer users than a between-user
A/B?**

<details>
<summary>Answer</summary>

Because the comparison happens inside each user's session. A
between-user A/B compares groups, so user-level variance is noise and
the test needs enough users to average it out. Interleaving shows both
variants to the same user, so that variance cancels within each
session — the executed feasibility read: 400 users for interleaving
against 10,000 for the A/B.

</details>

**2. The audit's two teams are equal, and the naive blend credits team
A with 59.2 percent. What does that mean?**

<details>
<summary>Answer</summary>

It means the blend, not the ranking, decided the winner. The naive
A-start list gives A the better positions (click mass 0.51 against
0.35), and users click whatever sits near the top regardless of
quality, so A collects clicks it did not earn. The random start
averages the two lists and lands at 49.7/50.3 — the 59.2 percent was a
position artifact. A fixed bias like this never shrinks with traffic:
at 200,000 sessions the naive interval excludes the true 50/50 by 78
standard errors.

</details>

**3. What does the credit rule have to decide before the experiment is
valid?**

<details>
<summary>Answer</summary>

What happens when a clicked document appears in both rankings. d2 was
proposed by both teams, so its credit is ambiguous — the tie rule
(first proposal, random split) decides it. Without the rule, shared
documents silently blur the comparison and the credit misstates which
team caused the click, which is the unbalanced-credit detour's point.

</details>

## Next

The measurement thread ends here and the frontier track moves to the
market: [stage 39 — first-price transition](../39-first-price-transition/),
where the winner pays its own bid and the price is set by what the
bidder bid, not what the ad was worth.

A detour from here: [the blend, not the ranking, can hand the win to
one team](when-the-blend-biases-the-credit/) — the executed
blend-variance audit: naive credits team A 59.3 percent against an
equal team B, at 200,000 sessions the interval misses the true 50/50
by 78 standard errors, and the random-start fix costs 3.6 percent more
sessions for the same interval width.

Another detour: [the traffic is too tiny for a between-user
A/B](when-the-traffic-is-tiny/) — the executed feasibility read: with
800 users the A/B never reaches significance (needs 10,000) while
interleaving needs 400 and ships.

Another detour: [the credit is unbalanced when both teams proposed the
clicked document](when-the-credit-is-unbalanced/) — the executed tie
read: d2 is in both rankings, so its click credits both teams and the
comparison blurs unless a tie rule decides.
