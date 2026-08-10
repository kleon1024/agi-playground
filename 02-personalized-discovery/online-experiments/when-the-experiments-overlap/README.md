---
status: verified
level: applied
base: scratch
label: When the experiments overlap
verified: 2026-08-08
---

# Whose number is it when two experiments share the traffic?

**Question:** [stage 54's gate](../) reads one experiment's verdict. This
chapter asks the platform question that has to be answered before the
second experiment starts: when two changes run on the same users, whose
number is each experiment's estimate?

**Before this:** [stage 54's gate](../) for the validity checks an
experiment passes, and [the split lies](../when-the-split-lies/) for the
sibling failure — a bucketing hash that drifts from the declared ratio.

## The collision, executed

The run ([record](runs/2026-08-08-overlap.md)) holds one cohort of 20,000
users and one outcome with a known truth: experiment A moves the metric by
1.0, experiment B by 0.5, and there is an interaction of 0.5 — when both
treatments are on, the metric moves by 2.0, not 1.5. Three platform
designs produce three answers.

| design | assignment correlation | A reports | B reports | sees the interaction |
|---|---:|---:|---:|---|
| naive shared bucket | 1.00 | 1.994 (p≈0) | 1.994 (p≈0) | no, and neither does anyone |
| layered randomization | 0.007 | 1.253 (truth 1.25) | 0.746 (truth 0.75) | no |
| 2x2 factorial | — | 1.035 at B-off, 1.466 at B-on | 0.521 at A-off, 0.952 at A-on | yes, 0.431 (truth 0.5) |

**The shared bucket is confident and wrong.** Both experiments hash the
same key and write to the same treatment flag, so every user is in the
same arm of both. Each experiment reads 1.994 with a tight p-value — the
sum of both effects plus the interaction — and both teams report the same
lift. Your number contains the other team's change entirely, and nothing
in the analysis says so. This is the failure mode behind "two teams
shipped, both measured the other's win".

**Layered randomization gives each experiment its own number.** Each
experiment owns a layer keyed to the user, hashed independently (Tang,
Agarwal, O'Brien and Meyer, 2010, KDD). Assignments are uncorrelated
(0.007), so A averages over B's 50/50 rollout and reports 1.253 against
the analytical truth A + interaction/2 = 1.25; B reports 0.746 against
0.75. Both main effects are unbiased, and the interaction is invisible to
both — by design.

**Only the 2x2 factorial sees the interaction.** Four cells from the two
layer assignments let you read A at B-off (1.035 vs 1), A at B-on (1.466
vs 1.5), B at A-off (0.521 vs 0.5), B at A-on (0.952 vs 1), and the
interaction itself (0.431 vs 0.5): the cell mean that is 2.0, not the
1.5 the two main effects predict.

## The reading

The three rows are not three analysis choices; they are three platform
behaviors that a team inherits. The shared bucket is the default when
bucketing is one global flag and nobody owns the layers — it produces the
most dangerous output, a tight p-value on someone else's effect. Layering
is the production default because it restores independence: every
experiment gets its own main effect averaged over everyone else's
rollouts, and teams stop stepping on each other. The price is interaction
blindness, which is acceptable until two changes touch the same funnel —
the ranker and the thumbnail, the price and the delivery window, the
model and the prompt. At that point the interaction is the decision
(Kohavi, Longbotham, Sommerfield and Henne, 2009, DMKD 18(1): interactions
in 2x2 designs are detected by the four-cell read, and the interaction
term is the difference between the joint and the additive prediction).

The interaction is not a niche corner case: it is why two individually
positive changes can ship and the combined metric moves less than either
predicted, or more. When the two changes are causally adjacent in the
same funnel, the factorial is the design that answers "what if both go
live", and that is the question the business actually ships.

## The fix and its trade

Run the experiments on independent layers, keyed to the user with a
per-layer salt, and escalate to a 2x2 factorial only when the two changes
touch the same funnel stage. The trade is analysis cost and power: a
factorial splits the traffic into four cells, so the per-cell sample is
half of what a two-arm experiment gets per condition, and the interaction
estimate has the largest variance of the three reads. Layering keeps
every experiment at full power for its own main effect, which is why it
is the daily default and the factorial is the deliberate escalation.
There is also an organizational half: the layer assignment must be owned
by the platform, not by each team's config, or two teams will quietly
reuse the same key and recreate the shared bucket.

## Who owns the loop

- **The experimentation-platform team** owns the layer keys and the
  per-layer salts, so two experiments cannot collide by reusing one hash
  key, and owns the escalation rule that sends same-funnel changes to a
  factorial.
- **The two product teams** own their experiments' hypotheses and read
  their own layer's main effect; they do not own the interaction.
- **The analytics team** owns the factorial read when it is escalated —
  the four-cell table and the interaction term — and reports the joint
  decision, not the two separate wins.

## Evidence boundary

The simulation is deterministic and synthetic: one outcome, known effects,
normal noise, 20,000 users, crc32 hashing. It demonstrates the mechanism —
what each platform design does to the estimate under a known interaction —
not the size of real interaction effects, which vary by change and funnel.
The citation-backed claims are the layered design itself (Tang et al.,
2010, KDD) and the 2x2 interaction read (Kohavi et al., 2009, DMKD).

## Check your mental model

**1. Why is the shared-bucket p-value dangerous if the estimate is wrong?**

<details>
<summary>Answer</summary>

Because the analysis machinery reports it as a real result: tight standard
error, p≈0, both teams reading the same number. There is no check that
flags "this estimate contains another experiment's effect". A wrong number
with high confidence ships, and the other team's change is silently
credited to you.

</details>

**2. When do you escalate from layering to a factorial?**

<details>
<summary>Answer</summary>

When the two changes touch the same funnel stage, so the interaction is
the question the business ships. Layering is the daily default because it
keeps every experiment's main effect at full power; the factorial pays
power to read the interaction, and that cost is only worth it when the
joint effect is the decision.

</details>

**3. Who prevents two teams from recreating the shared bucket?**

<details>
<summary>Answer</summary>

The experimentation platform, by owning the layer keys and per-layer
salts. If each team's config chooses its own bucketing key, nothing stops
two teams from hashing the same key and collapsing back into one shared
flag — the exact collision the layers were designed to remove.

</details>

## Next

Back to [stage 54's gate](../) for the rest of the validity conditions.
Two sibling detours complete the traffic picture: [the traffic is
two-sided](../when-the-traffic-is-two-sided/) — per-minute analysis rejects
53% of null switchbacks because the block, not the user, is the unit —
and [the user crosses groups](../when-the-user-crosses-groups/) — a
treatment session pollutes the next control session until a washout
removes it.
