---
status: verified
level: applied
base: scratch
label: When the slot hides the whale
verified: 2026-08-07
---

# The average displacement hides the one result that mattered

**Question:** [stage 18's audit](../) measures aggregate net ad value.
This chapter reads the executed distribution audit and asks what the
average hides when a slate carries one exceptionally valuable organic
item.

**Before this:** [stage 18 — ad externality](../) and its slice audit.

## The tail, executed

The run ([record](runs/2026-08-07-slot-whale.md)) draws 10,000
impressions: in 90 percent the whale ranks above the ad's slot and
displacement is small; in 10 percent the whale is the marginal item the
ad displaces:

| metric | displacement |
|---|---:|
| average | 0.2307 |
| P50 | 0.1557 |
| P90 | 0.9500 |
| P99 | 0.9500 |
| max (the whale) | 0.9500 |

## Two readings

**The mean is dominated by routine slots.** Median displacement is 0.1557;
the average 0.2307. Most impressions displace a small bottom item, and
the mean reports that. But one slate in ten displaces the whale — P90
through the max all sit at 0.9500, more than four times the average. The
same ad, the same load: the cost is a heavy-tailed distribution, not a
number.

**The tail is where the long-term value is.** The whale is the user's
single most valuable result — the product they were searching for, the
story that keeps the session alive. An externality decision priced on the
average treats the 10 percent tail as noise; the tail is precisely where
the ad destroys the value that retention and long-term worth depend on.
Blake, Nosko & Tadelis (2015, *Econometrica* 83(1):155-174) measured the
same substitution empirically at eBay — paid search ads on brand terms
produced little incremental value because the organic results they
displaced would have delivered it.

## The fix and its trade

The measured fix is to price the externality per slot and per context,
and to monitor the tail — P90/P99 displacement — alongside the mean, so
the whale contexts are priced, not averaged away. The value tree (stage
05) then admits an ad only when its net value clears the bar in the
contexts where the whale sits (Anderson & Coate, 2005, *Review of
Economic Studies* 72(4):947-972, derive the welfare trade of ad load in
a media market: the privately optimal ad load can exceed the socially
optimal one when the externality on content value is unpriced). The
trade is on the pricing side: per-context externality pricing is
expensive to estimate (each slot position needs its own measured
organic-value loss), which is why the mean keeps being used — and why
the tail monitor exists to catch what the mean hides.

## Who owns the loop

- **The value-tree and ranking team** owns tail-priced admission:
  per-context externality pricing that admits the ad only where the
  whale is not the marginal item.
- **The experimentation and measurement team** owns the tail monitor —
  P90/P99 displacement by slot position and user slice — the read that
  catches what the 0.2307 mean hides.
- **The ads product team** owns the whale-context policy: where the
  user's most valuable result sits, retention value beats the ad's
  marginal revenue.

## Evidence boundary

The executed distribution over 10,000 synthetic impressions with a fixed
seed (illustrative, deterministic). It demonstrates the heavy tail; real
displacement measurement comes from experiments that estimate
organic-value loss per position and per user slice, where the tail
quantiles are computed from logged outcomes rather than assumed.

## Check your mental model

Answer each before opening it.

**1. How can the average look cheap and the decision still be wrong?**

<details>
<summary>Answer</summary>

Because the average weights every impression equally and the tail is
rare. The measured mean is 0.2307 while P90 and P99 sit at 0.9500: most
impressions are cheap, one in ten is catastrophic. A revenue-vs-average-
displacement comparison keeps the ad because the average says so — while
the contexts where the user's most valuable result dies are exactly the
ones the average hid.

</details>

**2. What would you watch instead of the mean?**

<details>
<summary>Answer</summary>

The tail quantiles, stratified by context. The executed table is the
template: P90/P99 displacement against the mean, per slot position and
per user slice. When the tail clears the value-tree bar, the ad is
admitted only where the whale is not the marginal item — and the
quantile alarm catches the contexts where the externality concentrates
before the average ever moves.

</details>

## Next

Back to [stage 18](../), which closes the ads track — and with it, all
three of the mission's surfaces (recommendation 00-09, search 10-13,
ads 14-18). Return to [the mission README](../) for the full path.
