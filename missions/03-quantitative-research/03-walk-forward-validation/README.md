---
status: verified
verified: 2026-07-27
---

# What Sharpe would survive an honest split?

Your backtest says Sharpe 1.8. What number would it need for you to believe it?
The question is not whether 1.8 is large in isolation. It is whether the
process that produced it gave the strategy information that would have been
unavailable at the decision date, or selected it from enough alternatives that
a large winner was mechanically expected. Stage 01, `01-signal-research`,
records the alternatives tried. Stage 02 turns a score into target weights.
This stage tests the evaluation boundary before the cost and capacity stage is
allowed to price those weights.

The artifact is a set of walk-forward folds. A fold trains on the past and
tests on the next block. The core script uses the stage-00 price path, a
five-day forward label, and a fixed 20-day trailing-return feature; each fold
fits a linear direction rule on its own training rows. These constants were
chosen before this execution, not tuned to make a dramatic chart. The run has
1,255 AAPL bars and 1,230 usable labels. It reports the invalid shuffled
out-of-fold statistic, chronological unpurged statistic, and the
purged-and-gapped counterpart. Exact output lives in
[`runs/2026-07-27-walk-forward.md`](runs/2026-07-27-walk-forward.md). These figures come from a trailing window fetched on the run date; re-running the command pulls a newer window and shifts them slightly, which the run record explains.

## Which observations are allowed to teach the fold?

Ordinary k-fold cross-validation shuffles examples. In a market series that
puts future observations into the training set. That failure is obvious, but
chronological splitting has a quieter second failure. A label at date *t* can
mean the return from *t* through *t + 5*. A training label immediately before
a test block therefore consumes prices inside that test block. Its row looks
old, while its label has already reached across the boundary.

Serial correlation creates another reason to leave space. Adjacent rows share
the same market move, features, and overlapping label windows. A test row next
to a training row is not an independent future test merely because their
timestamps differ. **Purging** removes training observations whose forward
label overlaps the test window. In a strict past-only walk-forward fold, the
usual post-test embargo has no same-fold future training rows to remove, so the
implementation expresses that second protection as an additional pre-test
gap. They solve related but distinct boundary problems: overlap and
near-duplicate information.

<!-- interactive: PurgedFolds -->

Move the two windows. The default labels are the measured five-day run; the
counterfactual window changes are explicitly illustrative. More protection
usually reduces available data and can reduce an apparent statistic. That is
not a reason to choose a smaller window. The protected number is the one whose
claim has a defensible boundary.

The current fixed rule is a useful non-result. Each fold now fits a linear rule
on its declared training indices before scoring the test rows. Its
shuffled-invalid out-of-fold Sharpe was 0.7393, chronological unpurged Sharpe
0.9722, and purged-five-day, gapped-five-day Sharpe 0.9722. There was no
observed inflation in this one run. That does not license unpurged validation:
a guardrail is valuable precisely because it does not wait for a convenient
violation. It also demonstrates why no learner should expect the chapter to
arrange values for a prettier descending sequence.

## How much of the winner is just search?

Even a perfectly purged test does not erase selection. If N variants are
tested against the same history, the reported winner is the maximum of N noisy
estimates. A maximum is positive more often than an individual draw. Deflated
Sharpe asks whether the observed winner clears what search alone could create.
The core approximation subtracts an expected maximum-noise term and accepts a
trial count. With 14 disclosed trials, this run's protected statistic deflates
to 0.3145. It is a teaching approximation, not a claim that we estimated a
production probability.

The hard input is “effectively independent trials.” Nearby lookbacks and
thresholds are correlated, so counting every grid point as independent can
over-correct while counting a family as one can under-correct. Skew, kurtosis,
and the return-generating process are estimated too. Bailey and López de Prado,
“The Deflated Sharpe Ratio,” 2014, and their work on backtest overfitting make
this adjustment explicit; Harvey and Liu, “Backtesting,” 2015, document the
multiple-testing problem in asset pricing. Deflation is a lower bound on the
problem, not its cure.

The fold generator owns an explicit eligibility boundary. It receives a test
interval and constructs the blocked region, rather than hoping a generic
splitter knows the label definition. Change the forward horizon and the needed
purge changes with it; change a feature's information lag and the embargo may
change too. Version this configuration with the experiment so a reviewer can
reconstruct why every training row was eligible without trusting memory.

Run `uv run python core/walk_forward.py`. `prod/purged_walk_forward.py` shows
why `sklearn`’s `TimeSeriesSplit` supplies chronology but not purge or embargo;
a real implementation adds those operations and uses `scipy.stats` for the
distributional correction. The script is not investment advice and it has not
selected a strategy.

## What this still cannot establish

Passing this stage would rule out one class of self-deception, not establish a
working strategy. Regime change, transaction costs, capacity, point-in-time
fundamentals, and survivorship remain separate claims. `04-cost-and-capacity`
is next: it takes a paper portfolio and asks whether any economically useful
book can survive its own trading bill.
