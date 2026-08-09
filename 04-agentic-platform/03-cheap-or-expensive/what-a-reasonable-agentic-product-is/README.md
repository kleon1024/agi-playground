---
status: verified
level: frontier
base: none
label: A reasonable agentic product
verified: 2026-08-08
---

# When should the agent act, and when should a human sign it?

**Question:** the previous chapters established what the loop and its gates
do. This one asks the product question: which cells of an agent's behavior
should be fully automated, which should stop at a human, and what evidence
draws the line — before the market draws it for you.

**The artifact this chapter follows** is the routing table read from this
mission's recorded arms:

```text
arm / tier            delivered   $/delivered
no-harness haiku        0/6            —
no-harness sonnet       1/6           $1.3744
no-harness opus         3/6           $1.0924
harness haiku           6/6           $0.1604
harness sonnet          6/6           $0.5368
harness opus            6/6           $0.8226
public haiku            6/6           $0.1068
feedback-only pool      2/12          $1.5256
```

By the end you will be able to draw an automate-versus-gate line for an
agentic product, price both sides, and name the metric that tells you the
line is right.

**Before this:** [the governance chapter](../../04-how-it-fails/control-plane-governance/),
which priced the gates; this chapter decides where they sit.

## The failure mode: automating the wrong cell

The market's verdict on the value gap is already published. Gartner predicts
more than 40% of agentic AI projects will be canceled by end of 2027 —
escalating costs, unclear business value, inadequate risk controls
([Gartner, 2025-06-25](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)).
The cancellation is a product failure, not a model failure: the project
automated a cell whose delivery could not be verified, or gated a cell whose
delivery was never worth the friction. Both errors show up in the routing
table above as cells a product should not ship.

The unshippable cells are the blind arms: no-harness haiku delivered 0/6,
and every blind tier costs more per delivery than the corresponding harness
tier while delivering less. A product that surfaces the blind call as an
"agent" is selling the words, not the delivery — the exact failure the
intent chapter named, wearing a product label. Gating them does not fix
them; the cell should not exist.

## The automatable cells, and the second verdict

The cells that ship are the harness arms: 6/6 at every tier, with cost per
delivered outcome at \$0.1604 (haiku), \$0.5368 (sonnet), \$0.8226 (opus),
and the public set reproducing haiku's 6/6 at \$0.1068 on a previously
unseen codebase. The routing decision is not "which model" but "which model
at which price with the loop on": haiku-with-loop is the default, opus is
the escalation when the cheap tier's patches fail a verification the
product runs *after* resolve. Because stage 03's own runs found resolve
18/18 while generality measured 6/9 — three latent defects the given test
could not see — a shippable product needs a second verdict beyond the
target test, and the escalation policy is defined on that verdict, not on
resolve rate. This is the same discipline the 
[paradigm survey](../../../reference/research/agentic-paradigm-restructuring.md)
finds the agentic turn does not remove: generation replaces the ranked
surface, and verification replaces the score.

The price discovery in the ad market shows the same pattern from the other
side. OpenAI's sponsored messages launched at a \$60 CPM with a \$250,000
minimum, and the CPM eroded to about \$25 within ten weeks, forcing a shift
to cost-per-click bidding at \$3–\$5
([The Next Web, 2026-04-21](https://thenextweb.com/news/openai-chatgpt-cpc-ads-launch),
[the survey's ads section](../../../reference/research/agentic-paradigm-restructuring.md)).
A surface priced on impressions was gating nothing and delivering little;
the market repriced it on outcomes. That is this chapter's thesis in one
example: an agentic product's price must be per delivered outcome, or the
market will correct the price itself.

## The gated cells: payments and irreversibility

The cells that must stop at a human are the irreversible ones. The payment
rails that make agent transactions real — Mastercard's AP4M agent tokens and
Visa's tokenized credentials, June 2026
([surveyed here](../../../reference/research/agentic-paradigm-restructuring.md))
— give an agent a credential that can authorize spend across providers.
That is the enabling layer for agentic commerce and simultaneously the
clearest case for a gate: a wrong delivery here is money, and the
reversibility-based tiering from the governance chapter says the gate
appears exactly where damage cannot be undone. The evidence that the line is
right is the reversal rate: agents with automated eval coverage roll back at
9% versus 47% without it
([Forrester 2026, reported 2026-06-01](https://dev.to/milo_antaeus_784320e2f2f9/the-9-rollback-number-what-the-sinch-2026-study-is-actually-telling-you-2h3b))
— the metric this product should publish, because it is the one the market
is already using to decide which agents survive.

## The fix and its trade

The fix is a routing policy, not a feature: automate the cell where the
loop verifies and the price clears; gate the cell where delivery is
irreversible or the margin sits inside the run-to-run spread; delete the
cell that cannot deliver. The table above is the policy's evidence, and the
mission's own no-result — opus-tier blind margin inside its own spread —
is the template for what the policy must not claim. The trade is that the
policy is only as good as its two inputs: the verification step behind
resolve (the 6/9 generality gap is the standing reminder) and the reversal
telemetry that says the gate placement was right. A product that ships the
routing table without the second verdict ships the blind arm's confidence
at the harness's price.

## Who owns the loop

- **The product owner** owns the automate-versus-gate line and its
  published evidence: routing table, second verdict, reversal rate.
- **The pricing owner** owns the per-delivered-outcome price and the
  escalation curve — the market correction in the ad market is what happens
  when nobody owns it.
- **The risk owner** owns the gated cells: payments, irreversibility, and
  the human-approval path inside the loop's latency budget.

## Check your mental model

1. Two products both report resolve 6/6. One ships haiku-with-loop, the
   other ships the blind opus call. What distinguishes them?

<details>
<summary>Answer</summary>

Cost per delivered outcome and the second verdict. Haiku-with-loop delivers
6/6 at \$0.1604 per delivery; the blind opus call delivers 3/6 at \$1.0924
per delivery with no verification loop behind it. The 6/6 resolve rate
carries no routing information — stage 03's identical 18/18 across tiers
proved that — so the product distinction is the price per delivered outcome
and whether a verification beyond the given test exists.

</details>

2. Why is the reversal rate the metric that tells you the gate line is
   right?

<details>
<summary>Answer</summary>

Because it is the outcome of gate placement: too little gating shows up as
rollbacks (74% of enterprises have rolled back an agent; 47% without evals
vs 9% with), and too much gating shows up as delivered outcomes nobody uses.
The reversal rate is the market's own evidence for where the line should
be, which is why it belongs in the product's published metrics rather than
in postmortems.

</details>

## What this does not prove

**The routing table is this task set's table.** Two private tasks, three
tiers, three runs each, plus two public tasks — the per-cell numbers
characterize this mission's artifacts, and the no-result discipline is what
keeps them from overclaiming.

**Per-delivered pricing is not yet the agentic norm.** The ad market's shift
is one dated example of outcome repricing; the payment rails are enabling
infrastructure, and this chapter does not claim a settled market standard.

**The product shapes here are inference from measured and published
evidence, not a run of a product.** No agentic product was built, priced, or
rolled back in this mission; the reversal numbers are external records, and
the boundary is drawn from them plus this repo's runs, with both named.

**Next:** back to the [stage that started it](../../06-closing-the-loop/) — the
feedback-only slice is the smallest product that could still ship, and the
table above says exactly what it is missing (tools and a verification loop),
which is why 2/12 is a real but modest result.
