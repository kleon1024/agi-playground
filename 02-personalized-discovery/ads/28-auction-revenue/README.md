---
status: verified
level: applied
base: scratch
label: Auction revenue
verified: 2026-08-07
---

# The first-price revenue advantage erodes as bidders learn to shade

**Question:** [stage 14's second-price auction](../14-ad-auction/)
revealed value. This stage asks what the payment rule does to revenue,
and answers: the same bids pay different amounts under first- and
second-price — and the audit shows the first-price advantage is a
transient that erodes as bidders learn the rule.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the
auction mechanism, and [stage 27 — bid strategy](../27-bid-strategy/)
for where the bids come from.

## The mechanism, executed

The run ([record](runs/2026-08-07-auction-revenue.md)) executes the
same bids `[1.20, 1.00, 0.80]` under both payment rules:

| rule | winner pays |
|---|---:|
| first price | \$1.20 |
| second price | \$1.00 |
| gap | \$0.20 |

First price pays the winner's own bid; second price pays the
second-highest. The identical bids pay the platform 20 cents more per
auction under first price — but that gap is not free revenue:
advertisers know the rule and shade their bids, which is why the
honest-bidding property of stage 14 matters. Revenue per auction is
only half the question; bidder behavior under the rule is the other
half, and the [shading detour](when-first-price-pays-more/) executes
both.

## The failure mode, named and audited

**First-price revenue learns its way down.** The audit
([record](runs/2026-08-08-shading-dynamics.md)) plays a first-price
market for 12 rounds of 300 auctions (fixed seed) where three bidders
learn to shade against observed competition:

| round | mean revenue |
|---:|---:|
| 1 (naive) | 0.7485 |
| 2 | 0.6522 |
| 3 | 0.5903 |
| 5 | 0.5120 |
| 6 | 0.4998 |
| 10-12 (settled) | 0.4980 |

The verdict is measured: the naive round pays the winner's value at
0.7485; as the bidders best-respond to the competition they shade, and
revenue settles at 0.4980 — a 33 percent erosion to the symmetric
equilibrium, which for three uniform bidders is exactly the
second-price expected revenue (0.5000). The first-price advantage is a
transient, not a property: it exists only while bidders stay naive
(Vickrey, 1961, the revenue-equivalence result; Edelman, Ostrovsky &
Schwarz, 2007, and Varian, 2007, for the rules bidders adapt to;
Myerson, 1981, for the reserve as the platform's remaining lever).

**Revenue measured during the transition is not the revenue that
settles.** The [bidders-learn detour](when-the-bidders-learn/) reads
the same market at six points after a rule change: day one reads
0.7485 (+49.7 percent over second price), round 8 reads 0.5038 (+0.8
percent), and the settled read lands near the second-price level — a
day-one read that overstates the settled revenue by 57 percent. A
platform deciding on the early number over-invests in a rule whose
advantage is a transient (Google, 2019-09-04, moved Ad Manager to
first-price auctions expecting bidders to adapt; the settled market is
the one the platform lives with).

**The revenue comparison assumes the bidding behavior.** The
[first-price detour](when-first-price-pays-more/) narrows the gap from
\$0.20 to \$0.16 once bidders shade; the [reserve
detour](when-the-reserve-moves-revenue/) shows the reserve sitting on
the demand curve with its own optimum at \$0.8 (revenue 0.37). Both
are point-in-time reads of a curve that moves with the bidder
population — the audit's learning dynamics are the reason.

## Who owns the loop

The revenue only earns what someone is accountable for at each side of
the market loop, and each owner is tied to one of the failure modes
above:

- **The marketplace economics team** owns the revenue read and its
  window: which phase of bidder adaptation a measured number comes
  from, and the settled-state model. It owns the transient-as-property
  failure — the audit measured 0.7485 naive against 0.4980 settled, a
  33 percent erosion (Vickrey, 1961; Myerson, 1981).
- **The auction engineering team** owns the rule and the reserve: the
  mechanism bidders learn and the floor the platform sets. It owns the
  endogenous-lever failure — every platform action changes the
  distribution bidders best-respond to (Edelman, Ostrovsky & Schwarz,
  2007; Varian, 2007; Google's 2019 first-price transition as the
  industrial example).
- **The demand and bidder-facing team** owns the adaptation signal:
  shading estimates per bidder segment, win-margin trends, and the
  speed of convergence to equilibrium. It owns the
  invisible-transition failure — a market that looks great on day one
  and erodes over weeks is invisible to any report that averages
  across the window.

When the ownership is implicit, the economics team certifies revenue
from the transition period, engineering tunes the reserve against a
static demand model, and the platform invests in a rule whose
advantage is a third of what the naive read promised.

## Why this belongs in the mission

The mission's contract prices ads by revenue minus displacement. The
auction rule decides the revenue side, so choosing the rule is a
product decision with a measurable revenue shape — and the audit adds
the industrial detail: the shape moves. Revenue comparisons are only
valid for the bidding behavior they assume, bidders learn, and the
platform's levers (rule, reserve) are part of the game they learn.
That is why the settled state, not the day-one read, is the number
the market-design decision needs.

## Evidence boundary

The executed payment comparison over one bid set and the audit's
learning dynamics over 12 rounds of 300 synthetic auctions (fixed
seed, declared damping) are illustrative and deterministic. They
demonstrate the mechanism and the erosion; real revenue comparisons
use the bidder population's measured shading behavior, and real
transition measurement uses switchback or holdout markets rather than
a declared learning rule.

## Check your mental model

Answer each before opening it.

**1. Why is the 20-cent gap not free revenue?**

<details>
<summary>Answer</summary>

Because bidders anticipate the rule. Under first price the winner pays
its own bid, so rational bidders shade below value; the shading detour
shows the gap shrink from \$0.20 to \$0.16 once bidders shade. The
rule and the bidder population are coupled — the revenue comparison is
only valid for the bidding behavior it assumes.

</details>

**2. Your first-price launch report shows 50 percent more revenue than
second price. What do you check before celebrating?**

<details>
<summary>Answer</summary>

When the number was measured. The audit's market read 0.7485 on day
one — bidders still bidding truthfully — and settled at 0.4980 once
they learned to shade, equal to the second-price revenue. A day-one
read overstates the settled revenue by 57 percent. Check the bidders'
shading trend and the measurement window before treating the launch
number as the rule's revenue.

</details>

**3. What does the reserve do to the curve?**

<details>
<summary>Answer</summary>

It trades fill against price. A zero reserve fills every slot at zero
price; a high reserve prices each sale high but sells few. The
revenue-maximizing reserve sits between the two — \$0.37 at a \$0.8
reserve in the executed sweep — and is a property of the demand curve,
which is why it is estimated, not guessed.

</details>

## Next

Forward to [stage 29 — RTB pipeline](../29-rtb-pipeline/) where the
auction must run inside a 100ms deadline.

A detour from here: [first price pays more only when bidders stay
honest](when-first-price-pays-more/) — the executed shading read: naive
bidders pay \$1.20 under first price versus \$1.00 under second, but
shaded bidders narrow the gap to \$0.16, so the revenue comparison
assumes the bidding behavior.

Another detour: [the reserve sits on the demand
curve](when-the-reserve-moves-revenue/) — the executed sweep read:
expected revenue peaks at \$0.37 around a \$0.8 reserve, then falls as
fill collapses, so the reserve is estimated from the demand curve, not
guessed.

A third detour: [revenue measured during the transition is not the
revenue that settles](when-the-bidders-learn/) — the executed
measurement-window read: the same market reads +49.7 percent over
second price on day one and settles near it by round 18, so a day-one
read overstates settled revenue by 57 percent.
