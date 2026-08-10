---
status: verified
level: applied
verified: 2026-07-27
base: none
---

# What retrieves an item nobody has touched?

**Question:** stage 00 produced a behavioural log, and stage 02's two-tower and item-to-item queues learn from it. What retrieves an item with no interactions? Nothing in that log can: content is the only signal available before the first event.

The concrete artifact is a catalogue label and embedding. At time T, cold-item coverage is the fraction of catalogue items reachable by at least one queue. The behavioural queue reaches only items with logged interactions. Adding a content queue reaches items whose content can be labelled or embedded with enough confidence. That turns “help cold start” into a measurable union, rather than a slogan.

**Before this:** [stage 00's leak-free split and popularity baseline](../00-interactions/), which every queue in stage 02 — including the content queue this stage supplies — is ultimately measured against.

## Decide what the label is allowed to say

Label an item `phones` and retrieval improves, but nothing states that phones and laptops are both electronics — a hierarchy does. Build one, and a slate constraint can honestly say "at most two electronics items" because the shared parent sits in the taxonomy. Skip it, and the mixer needs a hidden lookup table instead — an undeclared taxonomy wearing a different name.

The core harness uses seven leaves under electronics, home, and media. This is deliberately small. The lesson is not that these are a useful production taxonomy; it is that the taxonomy determines what a diversity constraint, an audit, and a cold-start fallback can express. Taxonomies should be owned like product policy: changing one changes the feature contract for every downstream consumer.

There are three usual labelling paths. Hand rules are transparent and cheap, but fail on synonyms and incomplete metadata. A trained classifier can learn a local taxonomy when representative labels exist, but inherits sampling bias and has no magic answer for a new tail category. A vision-language model can read image and text evidence before interaction exists, but costs latency and money, and can confidently produce a wrong label. The production example uses a downloadable sentence-transformer embedding as a runnable text analogue; a VLM request would retain the same batch, response, confidence, and provenance contract.

Do not treat content and behaviour embeddings as substitutes. Behaviour tells you users co-engaged with two items — strongest signal for established inventory. Content tells you two items look or read alike — it exists on upload, but knows nothing about audience response. Reach for content retrieval first on a cold item; once enough events accumulate, let behaviour complement or supersede it. Treat either vector as ground truth and that boundary disappears.

## Move the confidence threshold

`core/content_understanding.py` builds synthetic short descriptions, interaction counts, keyword rules, and nearest centroids built from confident seed labels. Its constants are intentionally tuned to expose a substantial cold tail; they are disclosed in the code and are not measurements of a platform. Rules run first, then centroid matching fills zero-rule-hit items. The threshold is applied after that decision.

<!-- interactive: ColdStartCoverage -->

At threshold 0.00, the executed 300-item harness reached 100% of the catalogue through the union and 100% of the 112 cold items through content. At 0.65, label accuracy among retained items reached 100%, but cold coverage fell to 25% and union coverage to 72%. The behavioural queue stayed at 63% throughout. This is the essential trade: raising a threshold did not improve labels; it removed the least-certain labels, disproportionately from the tail the content queue exists to rescue.

Label noise is still consequential. A wrong hierarchical label can be amplified by recall, counted by diversity, boosted by editorial policy, and presented as a factual explanation. Confidence is not correctness. The demo's reported accuracy is only on synthetic items the harness already knows the answer for; in a real system, accuracy measured on convenient head samples says little about the tail. Tail annotation must be sampled and audited separately, because that is where the system has the least behavioural evidence and the strongest incentive to overclaim.

## The fix and its trade

The fix is the content queue itself: a label-and-embedding path that can
retrieve an item before any interaction exists, with a confidence threshold
chosen against a declared downstream objective and a sliced evaluation set.
The executed harness prices the mechanism — at threshold 0.00 the union
reaches 100% of the catalogue and 100% of the 112 cold items through
content; at 0.65 cold coverage falls to 25% while label accuracy among
retained items reaches 100%.

The trade, named: raising the threshold does not improve labels, it removes
the least-certain labels, disproportionately from the tail the content
queue exists to rescue. The behaviour queue is untouched (63% coverage at
every threshold) because its reach is a fact about the log, not a label
dial. And the deeper trade is provenance: a wrong hierarchical label can be
amplified by recall, counted by diversity, and presented as explanation, so
confidence is not correctness — tail annotation must be sampled and audited
separately. The fix buys cold-start reach at the price of owning the
taxonomy version, the model version, and the input hash alongside every
label, so a silent taxonomy-mix after backfill is impossible.

## Who owns the loop

- **The content and label team** owns the taxonomy and the label sources:
  what the label is allowed to say, which path produces it (rules,
  classifier, VLM), and the provenance record that makes an item's
  representation reproducible.
- **The model team** owns the threshold decision and its trade: the
  threshold is chosen against a declared objective and sliced evaluation
  set, never overall label accuracy.
- **The recall team** consumes the queue: the content route stands in for
  real learned embeddings until content understanding graduates from
  synthetic to production data, and cold coverage is this team's input to
  stage 02's union.
- **The evaluation team** owns the per-leaf precision and cold-coverage
  read, and the human review of the rejected and low-confidence tail.

## Reproduce and choose a production path

```bash
uv run python core/content_understanding.py
uv run python prod/sentence_transformers_label.py --catalogue-size 60
```

The production path requires `sentence-transformers` and downloads `all-MiniLM-L6-v2` on first use; it was not run here. Alternatives include a hosted multimodal embedding API and a fine-tuned image/text classifier. Their selection depends on taxonomy stability, annotation availability, batch cost, and whether image evidence is essential.

The run establishes the mechanics of a thresholded content queue on a synthetic catalogue. It does not establish VLM accuracy, tail accuracy, retrieval quality, or online discovery value. Stage 02 consumes this stage's content-derived route alongside behavioural queues and measures whether it retrieves a held-out target at all.

Retain more than a label. Store the taxonomy version, model or ruleset version, input content hash, confidence, label path, and processing time alongside it — that makes an item's representation reproducible when a policy changes, and stops a silent failure where the ranker mixes labels from two incompatible taxonomies after a backfill. Decide explicitly whether a queue accepts stale content labels, blocks until enrichment completes, or falls back to something coarse: these are availability decisions with user-facing consequences, not data-pipeline bookkeeping.

The threshold should be selected against a declared downstream objective and sliced evaluation set, never just overall label accuracy. A threshold that maximizes head accuracy can destroy reach for sparse categories. Inspect per-leaf precision, cold coverage, missing-content rate, and the share falling back to generic retrieval. Then sample the rejected and low-confidence tail for human review. The core cannot supply those numbers because it has no real catalogue; it only supplies the causal mechanism required to make them meaningful.

## Next

[Stage 02 — recall](../02-recall/) is where this stage's content labels and
embeddings stop being an isolated diagnostic: they become one of five
retrieval queues, standing in for real learned embeddings until content
understanding graduates from synthetic to production data.

A detour from here: [the confidence threshold: precision for the head, or
reach for the tail?](when-the-threshold-rescues-the-tail/) — the recorded
sweep read: raising the threshold to 0.65 cuts cold coverage from 100% to
25% while label accuracy only rises 96% to 100%, so the threshold is
trading the tail for the head.

Another detour: [the behavioural floor the threshold cannot
touch](the-63-percent-that-never-moves/) — the recorded sweep read:
behavioural coverage stays 63% at every threshold because the behaviour
queue's reach is a fact about the log, not a label dial.

A third detour: [the label the threshold cannot trust](when-the-label-is-noisy/) — the executed noise read: two of four kept items carry a wrong label, so precision is a property of the label source first and of the threshold second.
