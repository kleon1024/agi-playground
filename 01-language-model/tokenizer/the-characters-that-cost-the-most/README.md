---
status: verified
level: applied
base: scratch
label: The characters that cost the most
verified: 2026-08-08
---

# Some text costs an order of magnitude more

**Question:** [stage 01](../) freezes a tokenizer and reports one
aggregate number, chars per token — about 3.4 on its English corpus. This
chapter asks the question the aggregate hides: how much does each *class*
of text cost, and what does the difference do to a product that counts
tokens? The answer, measured on the real frozen tokenizer: English costs
0.24 tokens per character, CJK costs 2.96, and emoji costs 4.00 — a
fixed context window holds an order of magnitude less CJK text than
English text, and the mixed-document ledger shows why the aggregate
cannot see it.

**Before this:** [stage 01's tokenizer](../) for the byte-level BPE and
the freeze contract, and [the tie-break audit](../is-it-the-same-tokenizer/when-the-tie-break-matters/)
for the number-fragmentation mechanism this chapter prices. This chapter
is the per-class cost ledger the freeze never printed.

## The audit, executed

The run ([record](runs/2026-08-08-token-tax.md)) tokenizes a panel of
realistic inputs on the frozen `tokenizer.json` (16,384 ids, byte-level
BPE) and converts each rate into the context consequence:

| class | tokens per character | characters in a 4,096-token window |
|---|---:|---:|
| English prose | 0.24 | 17,246 |
| Code | 0.44 | 9,245 |
| Phone | 0.54 | 7,606 |
| Date | 0.60 | 6,826 |
| Big integer | 0.60 | 6,826 |
| Decimal | 0.62 | 6,553 |
| Accented Latin | 0.72 | 5,662 |
| CJK sentence | 2.96 | 1,382 |
| Emoji | 4.00 | 1,024 |

Two numbers carry the story. The tax varies by more than an order of
magnitude — a 27-character CJK sentence is 80 tokens, a 4-emoji string is
16 — and the context consequence is exactly what a product team feels: a
4,096-token window holds 17,246 characters of English but 1,382 of CJK.
The ledger makes the mechanism visible: in a mixed document, CJK is 4.3%
of the characters but 23.5% of the tokens, emoji 1.1% of the characters
but 7.8% of the tokens — digit, CJK, and emoji runs together are 17% of
the characters and 47% of the tokens.

## The failure mode, named

The aggregate is not wrong; it is blind. Chars-per-token is an average
over an English-heavy corpus, and averages hide tails — the exact failure
shape this curriculum names in every domain, from the recommendation
slice read to the reward-mix seesaw. Three product consequences follow
from the measured tax:

1. **The context budget is not fair.** A product that caps context at N
   tokens silently gives CJK users an effective window roughly one
   twelfth the size. Token pricing has the same shape: the same product
   text costs ~12x more in tokens per character for a Chinese user.
2. **The tokenizer chooses the model's language competence.** Tokenizer
   choice measurably changes downstream performance and training cost:
   Ali et al. trained 24 mono- and multilingual LLMs at 2.6B scale and
   found multilingual tokenizers need roughly 3x the vocabulary for the
   five most frequent European languages versus English, and that
   applying an English-centric tokenizer to multilingual training causes
   severe downstream degradation and up to 68% additional training cost
   (arXiv:2310.08754, Oct 2023). The measured tax here is the
   mechanism behind that cost.
3. **The arithmetic edge is the same story at small scale.** The big
   integer `1234567890` costs 6 tokens (`12|3|45|6|78|90`) because the
   pre-tokenizer caps digit runs at 3. How numbers tokenize changes
   arithmetic behavior on frontier models — left-to-right digit runs
   produce stereotyped errors concentrated on digit 4 (Singh and
   Strouse, arXiv:2402.14903, Feb 2024) — so a "model that cannot do
   arithmetic" is often a tokenization artifact, not a reasoning gap.

The documented industrial pattern matches the measured rates: non-Latin
scripts incur 3-5x token inflation relative to English across tokenizers
("Tokenization Disparities as Infrastructure Bias," arXiv:2510.12389,
Oct 2025).

## The fix and its trade

The fix has three parts, and each names its cost:

1. **Print the per-class ledger before freezing.** The run's mixed-document
   ledger is the release record's token-cost appendix: for every class the
   product serves, the share of characters versus share of tokens. The
   cost is a labeled class panel and a maintained one — the ledger has to
   be re-read when the corpus or the product language mix changes.
2. **Budget per class, not per token.** Context and pricing decisions use
   the class rates, not the aggregate: if the product serves CJK, the
   "4,096-token window" is really a "1,382-CJK-character window" until
   the tokenizer or the budget changes. The cost is that the budget
   becomes a per-language contract, which is harder to state in one
   number — the same price the reward-mix guardrail pays.
3. **Spend the finite vocab budget deliberately.** Merges are a fixed
   resource: every merge spent on CJK or number chunks displaces an
   English merge, and the measured 3x vocabulary requirement for
   multilingual coverage is the price of not doing it deliberately (Ali
   et al. 2023). The trade is embedding size and merge count against
   per-class cost — a vocab that covers CJK well is bigger, and a bigger
   vocab costs memory and training compute everywhere, not just on the
   classes it was added for.

The trade, named: there is no free lunch between the aggregate and the
classes. A tokenizer tuned for English is cheap and fast on English and
taxes everything else; a tokenizer tuned for the full language mix costs
3x the vocab and 68% more training when done after the fact (Ali et al.
2023). The audit is what lets the team choose which side of that trade it
is on, before the freeze makes the choice irreversible.

## Who owns the loop

The token tax is a data-health failure with a three-way handoff:

- **The tokenizer and training-data team** owns the vocab and the freeze:
  the per-class ledger in the release record, the digit-run cap, and the
  deliberate spend of the merge budget across the classes the product
  serves. It owns the choice, not the product consequence.
- **The evaluation team** owns the per-class boundary suite: the
  tie-break chapter's piece-level tests extended to a class panel —
  number-heavy strings, CJK, emoji, accented Latin — so the edge encodings
  are checked at every library swap, not discovered by users.
- **The product team** owns the per-class budget contract: which
  languages and formats the product serves, and what the token cost of
  each is allowed to be. When the ownership is implicit, the aggregate
  chars/token ships, the CJK window silently shrinks, and the "model is
  bad at Chinese" report lands on the model team instead of the
  tokenizer that chose it.

## Evidence boundary

The run measures the real frozen tokenizer on a hand-picked panel: the
per-class rates are exact for this tokenizer and these inputs, and the
ledger is exact for this document. The panel is not a corpus — real
mixed-language workloads have their own class distributions, so the
product consequence is a measured rate on representative inputs, not a
claim about every workload. The arithmetic consequence of number
fragmentation and the multilingual vocabulary cost are cited, dated
external results (Singh and Strouse 2024; Ali et al. 2023;
arXiv:2510.12389, Oct 2025). No model was trained here.

## Check your mental model

Answer each before reading on.

**1. Why does chars-per-token hide the token tax?**

Because it is an average over an English-heavy corpus, and the expensive
classes are the tail. CJK at 2.96 tokens per character and emoji at 4.00
get averaged into an English rate of 0.24, so the aggregate number is
true and useless at once — the ledger is the per-class read the average
cannot produce.

**2. What does "a 4,096-token context window" actually mean for a CJK
user?**

Measured here: the window holds 17,246 characters of English but 1,382 of
CJK — an order of magnitude less. Any product that caps context or prices
by token is silently giving non-English users a smaller window and a
higher bill, which is a product decision being made by the tokenizer
instead of by the team.

**3. Why is the number edge the same failure at small scale?**

The digit-run cap fragments large integers into per-digit pieces, the
same way the byte base fragments CJK characters — the pre-tokenizer
decides where the pieces break, and the pieces are what the model has to
align. Singh and Strouse (2024) show the break point changes arithmetic
behavior, so the fix is the same: audit where the edges break before the
freeze, not after the user reports it.

## Next

Back to [stage 01](../), where the freeze contract now has a per-class
ledger beside it. The number edge's downstream half is the arithmetic
behavior the tie-break chapter cites, and the context-budget consequence
connects to [mid-training's long-context story](../../02-pretrain/mid-training/),
where the token cost of a document stops being a curiosity and becomes
the budget a training run pays.
