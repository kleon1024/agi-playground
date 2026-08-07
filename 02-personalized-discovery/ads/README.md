---
status: draft
level: applied
---

# The ads track

An ad is a paid item that displaces an organic result. Everything else in this
track follows from that one sentence: the auction that decides who gets the
slot, the eCPM ranking that turns a bid and a click estimate into a position,
the calibration that makes the click estimate honest, the pacing that spends a
budget over a day instead of in the first hour, and the externality — the
organic result the ad pushed out — that the auction does not price.

## The build track (stages 14-18)

Each stage in this track carries three executed failure-mode detours:
the reserve that kills the sale, the honest bid, the one-bidder market
that makes the reserve the whole auction; the pCTR knife-edge, the
reserve that interacts with the rank, the tie-break rule that decides
when the estimate cannot; the correction that makes the estimate honest,
the ranking that is perfect while every value is wrong, the calibration
that drifts; the cap that binds when demand spikes, the budget that
pacing cannot create, the pacer that oscillates; the scarce slot, the
relevant ad, the whale slot that hides the externality. Every audit run
stratifies the failure by slice or by tail before it reports the
verdict, and each stage names who owns the loop.

| Stage | What it decides | Evidence |
|---|---|---|
| [`14-ad-auction`](14-ad-auction/) | The second-price auction, and truthful bidding | [verified](14-ad-auction/runs/) |
| [`15-ecpm-ranking`](15-ecpm-ranking/) | Bid × pCTR, and the lower bid that wins | [verified](15-ecpm-ranking/runs/) |
| [`16-ctr-calibration`](16-ctr-calibration/) | Making the click estimate honest | [verified](16-ctr-calibration/runs/) |
| [`17-budget-pacing`](17-budget-pacing/) | Delivering the budget under a per-hour cap | [verified](17-budget-pacing/runs/) |
| [`18-ad-externality`](18-ad-externality/) | The displacement trade, and when it amplifies | [verified](18-ad-externality/runs/) |

## The advanced track (stages 25-30)

| Stage | What it decides | Evidence |
|---|---|---|
| [`25-frequency-capping`](25-frequency-capping/) | The exposure cap as a value decision | [verified](25-frequency-capping/runs/) |
| [`26-creative-selection`](26-creative-selection/) | The per-context creative that feeds eCPM | [verified](26-creative-selection/runs/) |
| [`27-bid-strategy`](27-bid-strategy/) | Target-CPA bidding as value times conversion | [verified](27-bid-strategy/runs/) |
| [`28-auction-revenue`](28-auction-revenue/) | First vs second price, and the revenue rule | [verified](28-auction-revenue/runs/) |
| [`29-rtb-pipeline`](29-rtb-pipeline/) | The 100ms real-time bid as a selection mechanism | [verified](29-rtb-pipeline/runs/) |
| [`30-ads-measurement`](30-ads-measurement/) | Incrementality against a control | [verified](30-ads-measurement/runs/) |

## The frontier track (stages 38-42, 54)

| Stage | What it decides | Evidence |
|---|---|---|
| [`38-interleaving-experiments`](38-interleaving-experiments/) | Testing ads against organics in the same page | [verified](38-interleaving-experiments/runs/) |
| [`39-first-price-transition`](39-first-price-transition/) | What changes when the auction rule moves | [verified](39-first-price-transition/runs/) |
| [`40-privacy-safe-attribution`](40-privacy-safe-attribution/) | Attributing the conversion without the user trail | [verified](40-privacy-safe-attribution/runs/) |
| [`41-llm-creative-generation`](41-llm-creative-generation/) | The creative as generated text | [verified](41-llm-creative-generation/runs/) |
| [`42-marketplace-economics`](42-marketplace-economics/) | The marginal ad that stops paying for its displacement | [verified](42-marketplace-economics/runs/) |
| [`54-advertiser-roas`](54-advertiser-roas/) | The advertiser's return as the platform's revenue | [verified](54-advertiser-roas/runs/) |
