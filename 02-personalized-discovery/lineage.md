---
level: reference
---

# The open-source line behind personalized discovery

> Dated survey, 2026-08-06. Sources cited inline. External claims are not
> re-measured here; every repository claim cites the run that measured it.

**Question:** this mission's cascade — content understanding, multi-queue
recall, pre-rank, fine-rank, value tree, mixing — is how every production
recommender is shaped, and each stage is a line of open-source evolution with
its own tradeoff. This survey is the line, stage by stage, with the repo's
measured result at each point.

## From ratings to implicit signals

The **Netflix Prize** (2006-2009) established matrix factorization as the
field's center: **SVD** and **SVD++** (Koren, 2008-2009) factorized a
user-item matrix into low-rank embeddings, with implicit feedback folded in.
**ALS** (Hu et al., 2008) made the same idea work for implicit signals —
clicks, views, plays — where there is no rating to predict, only presence and
confidence. The tradeoff at this end of the line is expressiveness versus
scalability: full factorization is accurate and expensive; low-rank
approximations are cheap and lose the interactions they do not capture.

## Two-tower retrieval

**DSSM** (Huang et al., 2013) and the **YouTube DNN** (Covington et al., 2016)
split the problem in two: one tower embeds the query or user, the other the
item, and the score is a dot product. That shape exists because it is
approximate-nearest-neighbour friendly — embeddings can be precomputed and
searched, which is what makes recall over millions of items possible inside a
latency budget. The trade: a dot product cannot express cross features
("user who liked X wants Y"), so the tower pair gives up exactly the
interactions matrix factorization could express. **SASRec** (Kang et al.,
2018) and **BERT4Rec** (Sun et al., 2020) pushed the user tower from a fixed
embedding to a sequence model over interaction history, trading latency and
complexity for order-aware representation.

The repo's anchor is the cascade this line produces: recall over the full
catalogue, pre-rank cutting ~1,000 to ~100 with a model a hundredth of the
fine-ranker's cost, and the fine-ranker scoring a candidate set — because a
perfect ranker cannot rank an item that was never retrieved.

## Ranking and the position-bias line

**LambdaMART** (Burges, 2010) and the pairwise/listwise family made ranking a
learning problem over ordered pairs and lists rather than independent
scores. **Position bias** (Joachims et al., 2005) exposed the confound the
whole line must control: clicks are not relevance, they are relevance times
visibility, so unbiased-LTR methods (propensity weighting, logged-policy
correction) exist to keep the learner from optimizing the artifact of where
an item was shown.

## Slate assembly

Ranking items independently and taking top-K is wrong once a page is
consumed as a whole, which is the **maximal marginal relevance** insight
(Carbonell & Jaakkola, 1998) and the slate line after it (**DLCM**, 2018;
**SetRank**, 2019): the objective is over sets, and search is combinatorial,
so beam search and set-level losses replace pointwise scoring. The repo's
anchor: its mixing stage compares beam widths against the exhaustive optimum
on a nine-item catalogue — 2.2624 utility, matched at every width, which is
the measured claim that this constructed catalogue has no hard case, not a
license to trust narrow beams.

## Cold start

A new item has no clicks, so its embedding must come from its content — the
line from pure collaborative filtering to content-aware and hybrid models,
and the reason this mission's first stage labels items with a vision model
and measures cold-item coverage instead of assuming embeddings appear from
nowhere.

## Evidence boundary

This survey is dated and attributed, not measured. The repo's own anchors —
the cascade arithmetic, the 2.2624 exhaustive optimum, the p95 300ms serving
budget — cite the runs that produced them. What the line does not settle is
which stage should carry which model; that is this mission's measured
decision, stage by stage.
