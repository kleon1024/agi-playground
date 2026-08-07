---
status: verified
level: applied
base: scratch
label: When the slot is scarce
verified: 2026-08-06
---

# Scarcity amplifies the externality

**Question:** [stage 18's ad externality](../) showed every ad displaces
organic value. This chapter reads the executed slate-length sweep and asks
what scarcity does to the trade.

**Before this:** [stage 18 — ad externality](../) and its executed
displacement model.

## The curve, executed

The run ([record](runs/2026-08-06-scarcity-read.md)) sweeps the slate
length:

| slots | 1 ad displaces | share of slate |
|---:|---:|---:|
| 4 | 0.60 | 20.0% |
| 6 | 0.40 | 10.3% |
| 8 | 0.20 | 4.5% |

## Two readings

**The same ad displaces more when slots are scarce.** In a 4-slot slate
the displaced item is worth 0.60; in an 8-slot slate it is 0.20. The
externality is not a property of the ad — it is a property of the slot
supply. Scarcity amplifies it, which is why the ads decision cannot be
made without knowing the slate size.

**Slot count is part of the ad decision, not a constant.** A platform that
fixes "one ad per five results" is pricing displacement at one point on
the curve; a platform that varies slot count per context is choosing
where on the curve to sit. The value tree (stage 05) prices the
combination, and this sweep is the input that makes the choice explicit.

## Evidence boundary

The executed sweep over one hand-built organic-value list (illustrative,
deterministic, assumed ad utility). It demonstrates the scarcity effect;
real placement needs measured organic-value loss per position.

## Check your mental model

Answer each before opening it.

**1. Why does the same ad cost more organic value in a shorter slate?**

<details>
<summary>Answer</summary>

Because the ad pushes out a higher-ranked organic item. In a 4-slot slate
the ad takes the 4th slot, displacing the 4th-highest organic value
(0.60); in an 8-slot slate it displaces the 8th (0.20). The marginal
organic item at the ad's position is worth more when the slate is short,
so scarcity raises the cost of showing the ad.

</details>

**2. What does the share-of-slate column add to the absolute number?**

<details>
<summary>Answer</summary>

It prices the loss relative to what the slate offers. In a 4-slot slate
the displaced 0.60 is 20% of the slate's total value; in an 8-slot slate
0.20 is 4.5%. The same absolute loss is a bigger share of a short slate,
which is the metric the value tree needs to decide whether the ad's
revenue justifies the displacement.

</details>

## Next

Back to [stage 18](../), which closes the ads track — and with it, all
three of the mission's surfaces (recommendation 00-09, search 10-13,
ads 14-18). Return to [the mission README](../) for the full path.
