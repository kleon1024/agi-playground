---
status: draft
level: applied
---

# Shared discovery machinery

Every surface in this topic — recommendation, search, and ads — runs the same
decision loop: understand the item, retrieve a candidate set, rank it, mix it
into a slate, serve it inside a latency budget, and let the feedback come back
as the next round's training signal. What differs between the surfaces is the
input (no query, a query, a paid item with a bid) and the constraints (an
auction, a budget, an externality). The machinery is shared, so the shared
track is the spine and the search and ads tracks are its specializations.

## The build track (stages 00-09)

| Stage | What it decides | Evidence |
|---|---|---|
| [`00-interactions`](00-interactions/) | How a click is turned into a label the model may trust | [verified](00-interactions/runs/) |
| [`01-content-understanding`](01-content-understanding/) | What an item is, before it has any interactions | [verified](01-content-understanding/runs/) |
| [`02-recall`](02-recall/) | Which candidates the ranker is even allowed to see | [verified](02-recall/runs/) |
| [`03-pre-rank`](03-pre-rank/) | How a cheap model buys the fine ranker a smaller problem | [verified](03-pre-rank/runs/) |
| [`04-fine-rank`](04-fine-rank/) | The multi-objective score the slate is assembled from | [verified](04-fine-rank/runs/) |
| [`05-value-tree`](05-value-tree/) | How engagement, value, and revenue weights trade off | [verified](05-value-tree/runs/) |
| [`06-mixing`](06-mixing/) | How the slate is assembled, and where the ad goes in | [verified](06-mixing/runs/) |
| [`07-rule-engine`](07-rule-engine/) | The declarative constraints that override the score | [verified](07-rule-engine/runs/) |
| [`08-serving`](08-serving/) | The two-stage serving path inside the latency budget | [verified](08-serving/runs/) |
| [`09-report`](09-report/) | What the whole build proved, and what it did not | [verified](09-report/runs/) |

## The operations track (stages 43-55)

The build track ends where a deployed system starts. These stages are the
failure modes of a ranking system that is already live: the feature that
diverges between training and serving, the feedback loop that entrenches what
the ranker shows, the drift the offline eval cannot see, the peak that
capacity was never sized for, the user with no trail, and the economics that
decide whether the system pays for itself.

| Stage | What it decides | Evidence |
|---|---|---|
| [`43-feature-store`](43-feature-store/) | That training and serving read the same number | [verified](43-feature-store/runs/) |
| [`44-training-serving-consistency`](44-training-serving-consistency/) | When the offline eval reuses the broken world | [verified](44-training-serving-consistency/runs/) |
| [`45-feedback-loops`](45-feedback-loops/) | How the ranker's own output entrenches its input | [verified](45-feedback-loops/runs/) |
| [`46-retraining-and-staleness`](46-retraining-and-staleness/) | When the snapshot stops paying | [verified](46-retraining-and-staleness/runs/) |
| [`47-monitoring-and-drift`](47-monitoring-and-drift/) | How the world moving becomes visible | [verified](47-monitoring-and-drift/runs/) |
| [`48-realtime-user-state`](48-realtime-user-state/) | The session feature the batch model cannot see | [verified](48-realtime-user-state/runs/) |
| [`49-throughput-and-capacity`](49-throughput-and-capacity/) | Capacity as throughput times deadline | [verified](49-throughput-and-capacity/runs/) |
| [`50-cost-per-query`](50-cost-per-query/) | What serving actually costs per query | [verified](50-cost-per-query/runs/) |
| [`51-new-user-experience`](51-new-user-experience/) | Ranking for a user with no history | [verified](51-new-user-experience/runs/) |
| [`52-trust-and-explainability`](52-trust-and-explainability/) | When the explanation the user can check is wrong | [verified](52-trust-and-explainability/runs/) |
| [`53-fairness-and-allocation`](53-fairness-and-allocation/) | Exposure as a budget the ranker allocates | [verified](53-fairness-and-allocation/runs/) |
| [`54-online-experiments`](54-online-experiments/) | Whether a shipped change helped, read through a validity gate | [verified](54-online-experiments/runs/) |
| [`55-ltv-and-cac`](55-ltv-and-cac/) | Whether a user is worth acquiring and keeping | [verified](55-ltv-and-cac/runs/) |

The [`ads/`](../ads/) and [`recommendation/`](../recommendation/) tracks add
the surfaces' own stages; the [`search/`](../search/) track does the same for
the explicit-query loop.
