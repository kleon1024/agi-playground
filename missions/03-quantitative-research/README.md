---
status: draft
level: applied
---

# Quantitative research

**Business goal:** decide whether a candidate trading signal earns a place in
a systematic strategy book, without letting the act of searching for that
signal manufacture the appearance of skill it does not have.

Read [`mission.yaml`](mission.yaml) first, especially `does_not_prove`. This
mission teaches a method for evaluating a trading signal. It is not investment
advice, it recommends no security or strategy, and no money is ever at risk in
any of it.

## Why this mission exists

Mission 01 proved the language-model pipeline composes end to end. Mission 02
tested whether the same platform layers generalize to a different decision
loop — ranking — and found that the honest test is beating an embarrassingly
strong un-personalized baseline, on data that is confounded by the policy that
logged it.

This mission asks a harder question of the same architecture: does it
generalize to a domain where the data does not just sit there confounded, but
actively fights back? Text corpora and interaction logs are noisy, but the
relationships in them hold still while you study them. Markets do not. A
pattern a strategy discovers changes the moment enough capital trades on it,
because other participants are looking for the same pattern and will arbitrage
it away — a dynamic that has no analogue in next-token prediction or logged
clicks. Layer onto that a signal that is genuinely faint — the predictable
share of a daily return is a sliver of its total variance, and an information
coefficient that would be an embarrassing result in almost any other empirical
field counts as a real edge here — and you have a domain where almost any
modeling choice can be justified after the fact by a strategy that simply got
lucky on one slice of history. A model that looks good is more likely to be
overfit than skilled, and this mission is built to make that risk visible
rather than to paper over it.

## Why "it backtested well" is the wrong question

Test one strategy against history and a good Sharpe ratio is modest evidence
of skill. Test a hundred variants — different lookback windows, different
entry rules, different universes — against the *same* history, keep the best
one, and report only its number, and a good Sharpe ratio is nearly guaranteed
whether or not any of the hundred had a real edge. This is the multiple-testing
problem, and in quantitative research it is not a peripheral statistical
footnote; it is the central methodological problem of the field, playing the
role that confounded logged data plays in mission 02.

The mitigations exist because this failure mode is so easy to fall into by
accident. A **deflated Sharpe ratio** adjusts the observed Sharpe for the
number of trials that produced it, asking "how good would the best of N random
strategies look purely by chance?" and requiring the candidate to clear that
bar, not zero. **Walk-forward validation** — fit on a window, test on the
window immediately after it, roll forward — replaces a single train/test split
with a sequence of them, so a strategy has to keep working as the market
changes underneath it. And a random split, the way mission 02 warned against
for logged interactions, is worse here than there: financial labels are built
from overlapping windows (a 20-day return computed at every day overlaps the
next twenty computations), so a plain time split still leaks future
information across the boundary through that overlap. **Purging** removes
training examples whose label window overlaps the test period; **embargoing**
adds a gap after the test period before training resumes, so information
cannot leak backward through slowly-updating features either.

None of that is abstract. It is visible directly in what happens when you
simply try more strategies against one fixed history:

<!-- interactive: BacktestOverfit -->

Nothing before this widget's dividing rule is measured; every series in it is
labeled, seeded, and reproducible synthetic noise, not a market — and that is
the point. If the best-looking result climbs with the number of tries even
when nothing underneath has any edge at all, then "we tried many strategies
and this one looked best" is not evidence, and the evaluation harness this
mission builds — walk-forward folds, purge, embargo, deflated Sharpe — exists
specifically to keep that illusion out of the number this mission reports.

## Costs and capacity decide everything else

A strategy profitable before transaction costs and market impact is not a
strategy; it is an unfinished calculation. Every guardrail in
[`mission.yaml`](mission.yaml) forces costs to the front: net-of-cost Sharpe is
reported beside gross Sharpe rather than instead of it, so a gap between the
two is visible rather than quietly dropped; position size is capped against
trailing traded volume, so the backtest never assumes it can buy or sell more
than the market could plausibly absorb without moving the price against it.
Capacity is the sharpest version of this problem: a signal that works at
research scale can be unimplementable at the size a real book would need to
trade it, and a backtest that ignores this arithmetic is measuring a strategy
that cannot exist.

## The data problem underneath all of it

Every guardrail above assumes the input panel is honest, and a naive pull from
a market data source usually is not. A universe built from today's index
constituents silently drops every company that was delisted, acquired, or
went bankrupt during the study window — survivorship bias, and it biases
results in exactly one direction: better than reality, because the failures
are invisible by construction. Raw prices are wrong across a stock split or a
dividend unless corporate actions are backed out consistently. And a naive
join of a price on a given date to "the" fundamentals for that period is a
look-ahead violation, because that period's fundamentals were not public
knowledge until they were filed — often months later, and sometimes revised
afterward, so "the" value for a period is not even a single number. Getting
this wrong is not a rounding error; it is the difference between a backtest
that means something and one that has quietly already seen the future.
[Stage 00](00-market-data/) is where this gets fixed before anything is built
on top of it.

## Stages

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`00-market-data`](00-market-data/) | Point-in-time, corporate-action-adjusted, survivorship-bias-aware public market data panel | `platform/data` | Implementation present; run pending |
| [`01-signal-research`](01-signal-research/) | Candidate signal construction from point-in-time-only inputs, with a disclosed search log of every variant tried | new capability, mission-local | verified local run; mission outcome pending |
| [`02-cross-sectional-rank`](02-cross-sectional-rank/) | Rank the universe by signal and size target weights | `capabilities/rank-decide` | verified local run; mission outcome pending |
| [`03-walk-forward-validation`](03-walk-forward-validation/) | Purged, embargoed cross-validation folds; deflated Sharpe against the disclosed search log | `platform/evaluation-observability` | verified local run; mission outcome pending |
| [`04-cost-and-capacity`](04-cost-and-capacity/) | Transaction-cost and market-impact model; capacity-constrained position sizing | `platform/evaluation-observability` | verified local run with assumed costs; mission outcome pending |
| [`05-report`](05-report/) | Outcome versus both baselines and every guardrail, with regime-level failure cases | `platform/evaluation-observability` | verified evaluator run; outcome cannot determine |

## What this reuses

The point-in-time discipline in stage 00 is the same discipline
[`platform/data`](../../platform/data/) already teaches for training corpora:
know exactly what was knowable when, and do not let anything later leak
backward. Cross-sectional ranking and position sizing use the same
scoring-and-decide contract mission 02 built for recommendation and ads. That
contract has **not** been extracted into
[`capabilities/`](../../capabilities/) and should not be until this mission's
stages run: the promotion gate in
[`standards/mission-contract.md`](../../reference/standards/mission-contract.md) asks for
two missions sharing an input/output contract *and* an objective, and a rank
here maximizes risk-adjusted return where a rank there maximized engagement.
Naming the shared noun is not evidence that the decision is shared.
Walk-forward evaluation, harness disclosure, and variance reporting extend
[`platform/evaluation-observability`](../../platform/evaluation-observability/),
which already insists on seed variance and disclosed harnesses before mission
02's ranking numbers were credible; this mission adds purge, embargo, and
multiple-testing correction because financial evaluation needs strictly more
discipline than i.i.d. held-out data does, not less.

## Sequencing

Missions 01 and 02 establish the pipeline and prove one generalization claim
each. This mission is the third test of the same architecture, and the
hardest one: a domain chosen specifically because its data fights back, its
signal is faint, and the win condition is a number that has to survive
skepticism about how it was produced, not just what it says. What exists now
is the contract and the data stage — exactly what
[`standards/mission-contract.md`](../../reference/standards/mission-contract.md) requires
before anything past it gets built.
