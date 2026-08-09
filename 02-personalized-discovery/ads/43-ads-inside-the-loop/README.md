---
status: verified
level: frontier
base: none
label: Ads inside the loop
verified: 2026-08-08
---

# What survives of the auction?

**Question:** an ad used to be an item beside the content — a sponsored slot
in a ranked list. When the surface becomes an answer thread, the ad becomes a
step in the conversation the user is already in. This chapter asks what
survives of the auction, the budget machine, and the displacement trade, and
what actually changes.

**The artifact this chapter follows** is the displacement table, read from
this mission's own ad-externality run:

```text
ads  organic displaced   ad value      net
  1               0.3        0.6      0.3
  2               0.8        1.2      0.4
  3               1.5        1.8      0.3
```

By the end you will be able to say which parts of the ads loop a thread
surface keeps, which event it redefines as the conversion, and what the
displacement trade looks like inside an answer.

**Before this:** [stage 18](../../ads/18-ad-externality/),
[stage 17](../../ads/17-budget-pacing/), and
[stage 05](../../shared/05-value-tree/), whose runs this chapter re-reads,
and the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
that documents the surface shift.

## The failure mode: the ad that stopped being an item

The displacement table is the mission's contract stated in numbers: every ad
displaces an organic result. One ad displaces 0.3 of organic value for 0.6 of
ad value; three ads displace 1.5 for 1.8 — the net is positive but shrinking,
and the platform's value tree is where the trade rate decides how much organic
it may displace. When the ad moves inside an answer thread, this trade does
not go away; it sharpens. The user asked for something, and the ad is now
inside the answer to that request, so the displacement is no longer a slot on
a page — it is a step in the user's own intent.

The failure mode is therefore not that the auction breaks. It is that the
event the auction optimizes changes identity. In a ranked list, the conversion
is a click on the ad; in a thread, the conversion may be an agent-authorized
action — the booking, the purchase, the form fill the answer itself enables.
The [survey's ads section](../../../reference/research/agentic-paradigm-restructuring.md)
documents the real pricing trajectory of this shift: OpenAI launched sponsored
messages at a CPM of \$60 with a \$250,000 minimum spend, and within ten weeks
the CPM eroded to as low as \$25 and the model moved to cost-per-click bids of
\$3–\$5, with the minimum spend cut to \$50,000
([TNW, 2026-04-21](https://thenextweb.com/news/openai-chatgpt-cpc-ads-launch)).
A surface priced for brand impressions repriced to per-action within a quarter
— the market itself discovered that the thread conversion is the event.

## How you find the case

The recorded runs make the surviving machinery legible because each one tests
a mechanism the thread still needs. The displacement table shows the
externality is still the price of entry. The value-tree auction shows the gate
still runs: at `trade_rate=0.2` the ad does not clear, at `trade_rate=0.8` it
enters and displaces `item_6` at organic value 0.499 — the platform still
decides, arithmetically, how much organic it may displace for revenue. The
budget-pacing run shows delivery still binds: naive delivery exhausts the
budget at hour 3 under a morning spike, paced delivery survives the whole day
(88.4 spent, 11.6 unused).

The case-finding instrument is the contrast between what the thread changes
and what it does not. The thread changes the *surface* (the ad's position in
the loop) and the *conversion event* (click becomes authorized action). It
does not change the *machinery*: auction, trade rate, pacing, displacement
cost all survive in the recorded runs. The failure a thread-only reading
misses is the one the runs keep visible — a budget that exhausts at hour 3 is
the same failure in a thread as in a feed, and an ad that displaces 1.5 of
organic value is the same externality whether the organic item is a link or a
sentence in an answer.

## The fix and its trade

The fix is to keep the machinery and re-point the measurement: the auction
and the budget still decide, but the loop must measure the event the thread
actually monetizes, and must price the displacement inside the answer rather
than beside it. The trade is the pricing one the market already made. The
CPM-to-CPC shift is that trade in the open: impression pricing (\$60 CPM)
could not hold because impressions in a thread are not the scarce thing —
the user's intent and the authorized action are. Moving to CPC (\$3–\$5)
prices the event that converts, but it also moves risk onto the platform:
the ad only earns when the thread delivers an action, so the loop now owns
the conversion, not just the slot.

The second trade is the displacement one, unchanged in kind but sharper in
place. The value tree still sets the trade rate, and the displacement table
still prices it — but inside an answer, the displaced organic is the content
the user asked for, so the externality is now a trust cost, not just a
revenue trade. The fix cannot price that with the auction alone; it needs the
value-tree decision the mission already built, applied to a smaller, more
visible slate.

## Who owns the loop

- **The auction owner** owns the entry gate: the trade rate that decides
  whether the ad clears is unchanged, and it still prices displacement against
  organic value.
- **The delivery owner** owns the budget: pacing still binds, and the naive
  exhaustion failure at hour 3 is the same operational defect in a thread as
  in a feed.
- **The product owner** owns the conversion redefinition: the thread changes
  what counts as a sale, and the pricing evidence (CPM collapse, CPC move) is
  the market's read of that change, not an implementation detail.

## Check your mental model

1. The value-tree run shows the ad clearing only at `trade_rate=0.8`. Why
   does that gate survive when the ad moves from a feed slot into an answer
   thread?

<details>
<summary>Answer</summary>

Because the gate prices the trade, and the trade does not change: an ad inside
an answer still displaces organic content the user asked for. The trade rate
decides how much organic value the platform is willing to displace for ad
value — the same arithmetic question in a feed or a thread. What changes is
the content displaced (a sentence in the answer instead of a link on the
page) and the conversion event, not the decision the gate encodes.

</details>

2. OpenAI's CPM fell from \$60 to \$25 and the model moved to CPC within ten
   weeks. What does that pricing trajectory tell you about the event a thread
   surface actually sells?

<details>
<summary>Answer</summary>

It tells you the thread does not sell impressions — it sells actions. An
impression in an answer thread is cheap because the user's intent is already
there and the answer does the attention work; the scarce event is the
authorized action the thread can enable. The CPM collapse is the market
pricing that fact, and the CPC move is the platform accepting that it now
owns the conversion, not just the slot. The measurement question follows the
money: if the event is the action, the loop must attribute and verify actions,
not clicks.

</details>

## What this does not prove

**The displacement and pacing numbers are synthetic.** The externality model
and the pacing simulation run on declared synthetic inputs, not on a real
platform's bid distributions or demand curves; they prove the mechanisms, not
their real magnitudes.

**The auction entry is one seed's slate.** The `trade_rate=0.8` entry point is
read from a 12-item seed-42 run; the production solver in the same stage
bisects to a different rate (0.6039) for a 15% target ad load on 200 slates.
The gate's existence is the stable claim; the exact rate is not.

**The pricing trajectory is one company's 2026 snapshot.** The CPM and CPC
figures are TNW's reporting of OpenAI's sponsored messages, dated 2026-04-21;
they are evidence the market repriced the thread event, not a durable
equilibrium, and the [paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
says as much about every number it cites.

<!-- interactive: AdInThreadGate -->

**Next:** back to [the stage overview](../../) — or across to
[mission 04's intent-to-delivery chapter](../../../04-agentic-platform/05-report/intent-to-delivery/),
where the same loop is read from the harness side.
