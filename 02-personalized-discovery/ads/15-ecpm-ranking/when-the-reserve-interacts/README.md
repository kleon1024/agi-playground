---
status: verified
level: applied
base: scratch
label: When the reserve interacts
verified: 2026-08-06
---

# The reserve and the ranking are one decision

**Question:** [stage 14's reserve](../../14-ad-auction/) floors the auction,
and [stage 15's eCPM ranking](../) orders the ads. This chapter reads the
executed combination and asks how the two decisions interact.

**Before this:** [stage 15 — eCPM ranking](../) and its executed ranking.

## The combination, executed

The run ([record](runs/2026-08-06-reserve-ecpm.md)) applies the reserve
floor to three ads with eCPM 100 (Ad A), 150 (Ad B), and 120 (Ad C):

| reserve | eligible |
|---:|---|
| 0 | Ad A (100), Ad B (150), Ad C (120) |
| 100 | Ad A (100), Ad B (150), Ad C (120) |
| 125 | Ad B (150) |
| 160 | none |

## Two readings

**The reserve filters the ranking before the ranking orders it.** At
reserve 125, Ad A at 100 and Ad C at 120 are below the floor and out of
contention; only Ad B at 150 is even eligible. The floor does not reorder
the ads — it decides which ads get to be ordered at all.

**The floor and the ranking are one decision.** Raising the reserve is a
cheaper and more direct way to change what shows than re-ranking: at 160
the slot shows nothing, and no ranking of the three ads can override
that. Production sets the floor per slot or context, which is why the
reserve is part of the auction design (stage 14) rather than a separate
policy on top of it.

## Evidence boundary

The executed combination over three hand-built ads (illustrative,
deterministic). It demonstrates the interaction; real floor setting
optimizes against the demand distribution, balancing fill against
revenue.

## The fix and its trade

The measured fix is to set the floor from the same demand distribution
the auction stage sweeps, so the reserve and the ranking optimize the
same objective. The mechanism result is classical: the reserve is part
of the auction design, and its revenue effect must be analyzed with the
allocation, not after it (Vickrey, 1961, *Journal of Finance*; Myerson,
1981, *Mathematics of Operations Research*). In practice the floor is
re-tuned per slot or context against expected revenue, exactly as the
thin-market detour's hump sweep does. The trade is the executed 160 row:
every floor above the top eCPM prices the slot out entirely, so raising
the reserve trades fill for per-sale revenue — a decision that belongs
to the auction design (stage 14) and shows up in the ranking as a
missing competitor, not a reordering.

## Check your mental model

Answer each before opening it.

**1. Why does the reserve at 125 leave only Ad B?**

<details>
<summary>Answer</summary>

Because eligibility is a comparison of each ad's eCPM to the floor. Ad B's
150 clears 125; Ad A's 100 and Ad C's 120 do not. The floor is not a
ranking step — it is a gate before ranking. Everything below it is
refused outright, which is the difference between "worst ad shown" and
"no ad shown".

</details>

**2. What does the 160 row mean for the slot?**

<details>
<summary>Answer</summary>

That the floor can price the slot out of the market — no ad clears it, so
the slot runs without a paid item. That is the reserve's cost side: it
guarantees a minimum revenue per sold slot while risking no sale at all.
The executed sweep makes the trade visible: at 125 the slot sells at 150,
at 160 it sells nothing.

</details>

## Next

Back to [stage 15](../), or to
[the knife-edge the click estimate sits on](../when-pctr-moves-the-rank/)
for how sensitive the same ranking is to the pCTR that feeds it.
