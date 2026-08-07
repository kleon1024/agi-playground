---
status: verified
level: applied
base: scratch
label: When the tie-break matters
verified: 2026-08-07
---

# The same corpus, the same rule — why two vocabularies?

**Question:** the parent chapter held one thing fixed to make two
implementations comparable: the rule that breaks ties. This detour asks what
happens when that rule is not the same — the situation a team is actually in
when it swaps a tokenizer library. BPE says "merge the most frequent pair",
but real text is full of pairs with *equal* counts. Whoever wins a tie is
arbitrary. Does that choice change the vocabulary, can the usual metrics see
it, and does it land anywhere a downstream model cares?

**Before this:** [how do you know the fast version learned the same
vocabulary?](../) showed that a speedup is only safe if it produces the
*identical* merge list, and that the comparison only works because both
implementations break ties the same way. You need that argument before the
question here has teeth: if the tie-break were free to vary, "identical" would
not even be defined. The [merges that build the vocabulary](../../the-merges-that-build-the-vocab/)
is where merge mechanics are established.

## The tie is the norm, not the corner case

The audit ([run record](runs/2026-08-07-tie-break-audit.md)) trains the same
indexed BPE twice on the same 8,500 no_robots training turns, under two
deterministic tie-break rules, at a 4,096 vocabulary. Out of 3,840 merge
steps, **91.7% chose from a tie** — the mean tie width is 25.7 pairs, the
widest 194. The "most frequent pair" instruction is a partial order; the tie
is what the algorithm actually does most of the time. So the tie-break is not
a rare edge a team can ignore: it is exercising real decision-making power on
essentially every merge, and the only question is which arbitrary rule is
silently deciding.

That is why the parent chapter's insistence on one fixed rule is not
pedantry. It is what makes two implementations *comparable at all*.

## One tie cascades into a different vocabulary

A merge is not an isolated choice. Merging one pair creates new pairs and
rewrites the counts around it, so an early tie-break decision propagates. The
run measures that propagation directly: the two rules pick their first
different pair at **merge step 132**, and from there the merge sets diverge
permanently. Jaccard overlap at depths 500, 1,000, 2,000, and full is
**0.508, 0.506, 0.534, 0.541** — the two vocabularies share only about half
their merge decisions by the end.

The sequence matters, not just the counts: token ids depend on merge order,
so a swapped tokenizer library that breaks ties differently does not produce
the same token ids for the same text. A model trained on one vocabulary and
served with the other is silently speaking a different language — the exact
invisible corruption the parent chapter's export check was built to catch,
now caused not by a bug but by a convention.

## The standard metric cannot see the divergence

Here is the part that makes this failure mode dangerous. Held-out text
encodes at **3.418 chars/token under the lex rule and 3.416 under reverse-lex**
— identical within rounding. A team comparing two tokenizer implementations
by chars/token, by tokens-per-second, or by downstream loss sees no signal.

The segmentation disagrees anyway: **41.0% of held-out pieces (39,525 of
96,383) encode to a different token sequence** between the two vocabularies.
The divergence is almost entirely *which* tokens — only 250 pieces differ in
token *count*. Aggregate compression is a sum over pieces, and it is
insensitive to *how* the same number of pieces is cut. The metric that is
easiest to check is the one least able to see this class of change.

## The difference lands on the edges a model cares about

Where do the two vocabularies disagree? Read the edge encodings in the run
record. A sentence containing 1,234,567,890 splits per-digit — `12|3|4|5|6|7|8|9|0`
— because the pre-tokenizer caps digit runs at `\d{1,3}`. CJK characters
fragment to 3 pieces each through the 256-byte base; accented characters split
to 2 pieces. These are the exact edges where real production tokenizers
differ: digit-run handling, byte fallback, and rare-character coverage are
where implementations make different choices, and the choices are not
equivalent downstream.

The magnitude of the downstream effect is not speculative. Singh et al.,
[Tokenization counts](https://arxiv.org/abs/2402.14903) (Feb 2024), show that
how numbers tokenize measurably changes arithmetic behavior on frontier
models: comma-separated, right-to-left number tokenization (the "r2l" style)
improves GPT-3.5/GPT-4 arithmetic accuracy, while left-to-right digit runs
produce stereotyped errors concentrated on digit 4. The tokenizer's
tie-break decides which of these regimes a vocabulary lands in, because it
decides which pieces the digit runs and rare characters become.

## Who owns it

The tokenizer and training-data teams own the tie-break as a **contract**:
the rule, the pre-tokenizer digit cap, and the byte base are pinned in the
frozen tokenizer.json, and any library swap must reproduce the merge sequence
— the parent chapter's exact-id check is the acceptance test. The eval team
owns boundary tests that do not trust the aggregate: a held-out suite that
compares *piece-level* segmentation and includes number-heavy and
rare-unicode strings, not just chars/token. The model team owns the
consequence: a vocabulary whose number pieces fragment per-digit is a
measurable arithmetic handicap before a single weight is trained.

When nobody owns the tie-break, the symptom shows up as a "mysterious"
divergence after a library upgrade: the model serves fine, the corpus metrics
look identical, and the first real cost appears downstream as bad arithmetic
or rare-character handling — attributed to the model, the data, or the seed
before the line that chose the tie.

## What this chapter does not prove

This is a mechanism demo at a toy vocabulary (4,096, not the mission's
16,384), on one curated corpus, under two fixed deterministic rules. It proves
the divergence mechanism exists and measures its shape; it does not train a
model, so it does not measure the end-to-end behavioral cost — that magnitude
is cited to Singh et al. above rather than asserted. Production tokenizers
also differ in pre-tokenizer digit rules and byte handling, which this run
holds fixed; real-world differences are therefore at least as large as what
is measured here.

## Check your mental model

Answer each before opening it.

**1. Why is the tie the norm rather than the exception?**

<details>
<summary>Answer</summary>

Because the count distribution is heavy: a few pairs dominate, and below them
a long tail of pairs sits at similar, low frequencies. When the maximum count
is a band of near-equal pairs rather than a unique pair, the algorithm must
pick among several — 91.7% of merge steps here did. The tie is what the
algorithm actually does; the unique maximum is the special case.

</details>

**2. Why can chars/token look identical while 41% of pieces differ?**

<details>
<summary>Answer</summary>

Chars/token is a sum over the whole corpus: it averages away *how* pieces are
cut, keeping only the total. Two segmentations can cut the same text into the
same number of pieces with the same average length while disagreeing on
almost every boundary — 41.0% of pieces differed here while the aggregate
matched within rounding. The metric that is easiest to compute is the one
least sensitive to this class of change; piece-level comparison is the check
that sees it.

</details>

**3. Why does the number edge fragment, and why should a model team care?**

<details>
<summary>Answer</summary>

The pre-tokenizer caps digit runs at three digits (`\d{1,3}`), and at a small
vocabulary no merged digit piece exists, so long numbers encode per-digit
(`12|3|4|5|6|7|8|9|0`). Per-digit pieces remove the positional structure that
lets a model treat "1230" as a unit. Singh et al. (2024) show the choice of
number tokenization measurably changes arithmetic on frontier models —
right-to-left grouping helps, left-to-right digit runs produce systematic
errors. The tokenizer's conventions, including tie-break, decide which regime
the model lives in.

</details>

## Next

Return to [freeze it before you go on](../../README.md#freeze-it-before-you-go-on)
with the tie-break now named as part of what the frozen file pins. The same
invisible-convention lens is what [stage 02's curve divergence](../../../02-pretrain/when-the-curve-goes-wrong/)
deals with at the optimizer level, and what [stage 04's reward
audit](../../../04-rl/reward-went-up/when-the-reward-is-wrong/) deals with at the
label level: a hidden axis that the usual metrics cannot see.
